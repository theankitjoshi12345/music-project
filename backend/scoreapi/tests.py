from django.test import SimpleTestCase
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
import tempfile
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from pathlib import Path
from rest_framework.test import APITestCase

from .models import Passage, PracticeMark, Score
from .score_extract import OMRUnavailable, PDFExtraction
from .upload_service import store_upload


class HealthCheckTests(SimpleTestCase):
    def test_health_check_endpoint(self):
        response = self.client.get(reverse("scoreapi:health-check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "score-companion-api"})


class ScoreApiTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        media = tempfile.TemporaryDirectory(prefix="score-api-tests-")
        cls.addClassCleanup(media.cleanup)
        settings = override_settings(MEDIA_ROOT=media.name)
        settings.enable()
        cls.addClassCleanup(settings.disable)

    def setUp(self):
        self.score = Score.objects.create(
            title="Symphony No. 1",
            movement="Movement I",
            instrument="Percussion",
            page_count=4,
            available_offline=True,
        )
        self.other_score = Score.objects.create(
            title="Symphony No. 1",
            movement="Movement II",
            instrument="Percussion",
            page_count=4,
            available_offline=True,
        )
        self.passage = Passage.objects.create(
            score=self.score, section="B", measure_number=24, page_number=2
        )
        self.other_passage = Passage.objects.create(
            score=self.other_score, section="A", measure_number=1, page_number=1
        )

    def test_health_check_is_preserved(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_score_list_and_detail_include_library_context(self):
        response = self.client.get("/api/scores/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        first_score = next(item for item in response.json() if item["id"] == self.score.id)
        self.assertEqual(first_score["passage_count"], 1)
        self.assertTrue(first_score["available_offline"])

        detail = self.client.get(f"/api/scores/{self.score.id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["movement"], "Movement I")

    def test_pdf_upload_creates_an_offline_library_entry_for_manual_measure_setup(self):
        response = self.client.post(
            "/api/scores/upload/",
            {
                "score_file": SimpleUploadedFile("winter-song.pdf", b"%PDF-1.4 placeholder"),
                "instrument": "Clarinet",
                "page_count": "3",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["instrument"], "Clarinet")
        self.assertEqual(response.json()["page_count"], 3)
        uploaded = Score.objects.get(pk=response.json()["id"])
        self.assertTrue(uploaded.available_offline)
        self.assertEqual(uploaded.passages.count(), 0)

    def test_musicxml_upload_extracts_real_measures_and_can_be_marked_for_practice(self):
        musicxml = b'''<score-partwise><part id="P1"><measure number="1"/><measure number="2"><direction><direction-type><rehearsal>A</rehearsal></direction-type></direction></measure><measure number="3"><print new-page="yes"/></measure></part></score-partwise>'''
        response = self.client.post(
            "/api/scores/upload/",
            {"score_file": SimpleUploadedFile("three-measures.musicxml", musicxml)},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        score = Score.objects.get(pk=response.json()["id"])
        self.assertEqual(score.page_count, 2)
        self.assertEqual(list(score.passages.order_by("page_number", "measure_number").values_list("section", "measure_number", "page_number")), [("Start", 1, 1), ("A", 2, 1), ("A", 3, 2)])

        created = self.client.post(
            f"/api/scores/{score.id}/passages/",
            {"section": "B", "measure_number": 4, "page_number": 2},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        mark = self.client.post("/api/practice-marks/", {"passage_id": created.json()["id"]}, format="json")
        self.assertEqual(mark.status_code, 201)

    def test_reupload_reuses_file_measures_and_practice_notes(self):
        original = self.client.post("/api/scores/upload/", {
            "score_file": SimpleUploadedFile("part.pdf", b"%PDF original part"),
        }, format="multipart")
        score = Score.objects.get(pk=original.json()["id"])
        passage = Passage.objects.create(score=score, section="Page 1", measure_number=1, page_number=1)
        mark = PracticeMark.objects.create(passage=passage, note="Keep this note")
        score.extraction_state = "complete"
        score.save()
        before_files = set(Path(settings.MEDIA_ROOT).rglob("*.*"))
        repeated = self.client.post("/api/scores/upload/", {
            "score_file": SimpleUploadedFile("renamed-part.pdf", b"%PDF original part"),
            "title": "Do not overwrite the original title",
        }, format="multipart")
        self.assertEqual(repeated.status_code, 200)
        self.assertTrue(repeated.json()["already_uploaded"])
        self.assertEqual(repeated.json()["id"], score.id)
        self.assertEqual(repeated.json()["extraction_status"], "complete")
        self.assertEqual(repeated.json()["passage_count"], 1)
        self.assertEqual(set(Path(settings.MEDIA_ROOT).rglob("*.*")), before_files)
        score.refresh_from_db()
        self.assertEqual(score.title, "part")
        mark.refresh_from_db()
        self.assertEqual(mark.note, "Keep this note")

    def test_different_files_with_the_same_name_never_overwrite_each_other(self):
        responses = [self.client.post("/api/scores/upload/", {
            "score_file": SimpleUploadedFile("same.pdf", content),
        }, format="multipart") for content in [b"%PDF first", b"%PDF second"]]
        self.assertEqual([response.status_code for response in responses], [201, 201])
        files = [Score.objects.get(pk=response.json()["id"]).source_file for response in responses]
        self.assertNotEqual(files[0].name, files[1].name)
        self.assertEqual(files[0].read(), b"%PDF first")
        self.assertEqual(files[1].read(), b"%PDF second")

    def test_import_database_failure_rolls_back_score_and_cleans_the_file(self):
        before_files = set(Path(settings.MEDIA_ROOT).rglob("*.*"))
        before_count = Score.objects.count()
        response = self.client.post("/api/scores/upload/", {
            "score_file": SimpleUploadedFile("invalid.musicxml", b'<score-partwise><part><measure number="1"/><measure number="1"/></part></score-partwise>'),
        }, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Score.objects.count(), before_count)
        self.assertEqual(set(Path(settings.MEDIA_ROOT).rglob("*.*")), before_files)

    def test_losing_a_duplicate_upload_race_returns_winner_and_cleans_extra_file(self):
        metadata = {"title": "Winner", "movement": "Part", "instrument": "Piano", "page_count": 1}
        winner, _ = store_upload(SimpleUploadedFile("winner.pdf", b"%PDF race"), metadata, [])
        before_files = set(Path(settings.MEDIA_ROOT).rglob("*.*"))
        with patch("scoreapi.upload_service.Score.objects.filter") as lookup:
            lookup.return_value.first.side_effect = [None, winner]
            score, created = store_upload(SimpleUploadedFile("loser.pdf", b"%PDF race"), metadata, [])
        self.assertFalse(created)
        self.assertEqual(score.id, winner.id)
        self.assertEqual(set(Path(settings.MEDIA_ROOT).rglob("*.*")), before_files)

    def test_repeated_measure_save_is_idempotent_and_wrong_pages_are_rejected(self):
        url = f"/api/scores/{self.score.id}/passages/"
        values = {"section": "A", "measure_number": 1, "page_number": 1}
        first = self.client.post(url, values, format="json")
        repeated = self.client.post(url, values, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(first.json()["id"], repeated.json()["id"])
        conflict = self.client.post(url, {**values, "page_number": 2}, format="json")
        self.assertEqual(conflict.status_code, 409)
        invalid = self.client.post(url, {**values, "measure_number": 2, "page_number": 99}, format="json")
        self.assertEqual(invalid.status_code, 400)

    def test_deleting_a_score_removes_its_passages_and_practice_marks(self):
        mark = PracticeMark.objects.create(passage=self.passage)
        response = self.client.delete(f"/api/scores/{self.score.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Score.objects.filter(pk=self.score.id).exists())
        self.assertFalse(Passage.objects.filter(pk=self.passage.id).exists())
        self.assertFalse(PracticeMark.objects.filter(pk=mark.id).exists())

    @override_settings(AUDIVERIS_COMMAND="/opt/audiveris")
    @patch("scoreapi.extraction_service.extract_pdf_measures", return_value=PDFExtraction([("Page 1", 1, 1), ("Page 1", 2, 1), ("Page 2", 3, 2)], 2))
    def test_pdf_extraction_preserves_existing_passages_and_practice_marks(self, extract_pdf):
        score = Score.objects.create(title="Scan", movement="Scan", instrument="Piano", page_count=1, available_offline=True, source_file=SimpleUploadedFile("scan.pdf", b"%PDF"))
        passage = Passage.objects.create(score=score, section="Page 1", measure_number=1, page_number=1)
        mark = PracticeMark.objects.create(passage=passage, note="Keep this reminder")
        response = self.client.post(f"/api/scores/{score.id}/extract-measures/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["passage_count"], 3)
        self.assertEqual(response.json()["page_count"], 2)
        self.assertEqual(response.json()["extraction_status"], "complete")
        self.assertEqual(Passage.objects.filter(score=score).count(), 3)
        mark.refresh_from_db()
        self.assertEqual(mark.passage_id, passage.id)
        self.assertEqual(mark.note, "Keep this reminder")
        repeated = self.client.post(f"/api/scores/{score.id}/extract-measures/")
        self.assertEqual(repeated.status_code, 200)
        extract_pdf.assert_called_once()

    @patch("scoreapi.extraction_service.extract_pdf_measures", side_effect=OMRUnavailable("Install Audiveris to retry."))
    def test_runtime_failure_is_reported_and_does_not_delete_existing_data(self, extract_pdf):
        self.score.source_file = "scores/scan.pdf"
        self.score.save()
        response = self.client.post(f"/api/scores/{self.score.id}/extract-measures/")
        self.assertEqual(response.status_code, 503)
        detail = self.client.get(f"/api/scores/{self.score.id}/").json()
        self.assertEqual(detail["extraction_status"], "failed")
        self.assertIn("Audiveris", detail["extraction_error"])
        self.assertTrue(Passage.objects.filter(pk=self.passage.id).exists())

    @patch("scoreapi.extraction_service.extract_pdf_measures")
    def test_concurrent_extraction_does_not_launch_a_second_job(self, extract_pdf):
        self.score.source_file = "scores/scan.pdf"
        self.score.extraction_state = "processing"
        self.score.extraction_updated_at = timezone.now()
        self.score.save()
        response = self.client.post(f"/api/scores/{self.score.id}/extract-measures/")
        self.assertEqual(response.status_code, 409)
        extract_pdf.assert_not_called()

    def test_manual_placeholder_does_not_claim_pdf_extraction_succeeded(self):
        self.score.source_file = "scores/scan.pdf"
        self.score.save()
        response = self.client.get(f"/api/scores/{self.score.id}/")
        self.assertEqual(response.json()["extraction_status"], "not_started")

    @patch("scoreapi.extraction_service.extract_pdf_measures", return_value=PDFExtraction([("Page 1", 1, 1)], 1))
    def test_interrupted_job_can_be_retried_instead_of_showing_progress_forever(self, extract_pdf):
        self.score.source_file = "scores/scan.pdf"
        self.score.extraction_state = "processing"
        self.score.extraction_updated_at = timezone.now() - timedelta(minutes=20)
        self.score.save()
        detail = self.client.get(f"/api/scores/{self.score.id}/").json()
        self.assertEqual(detail["extraction_status"], "failed")
        self.assertIn("interrupted", detail["extraction_error"])
        response = self.client.post(f"/api/scores/{self.score.id}/extract-measures/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["extraction_status"], "complete")

    def test_passages_are_limited_to_the_requested_score(self):
        response = self.client.get(f"/api/scores/{self.score.id}/passages/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [
            {
                "id": self.passage.id,
                "section": "B",
                "measure_number": 24,
                "page_number": 2,
                "is_marked_for_practice": False,
            }
        ])

    def test_create_mark_and_filter_unresolved_marks(self):
        response = self.client.post(
            "/api/practice-marks/",
            {"passage_id": self.passage.id, "note": " Keep the rhythm even. "},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["note"], "Keep the rhythm even.")
        self.assertFalse(response.json()["is_resolved"])
        self.assertEqual(response.json()["passage"]["measure_number"], 24)
        self.assertEqual(response.json()["passage"]["movement"], "Movement I")

        listing = self.client.get(
            f"/api/practice-marks/?score={self.score.id}&status=unresolved"
        )
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.json()), 1)

    def test_duplicate_save_is_idempotent_and_invalid_status_is_rejected(self):
        mark = PracticeMark.objects.create(passage=self.passage, note="Preserve my note")
        duplicate = self.client.post(
            "/api/practice-marks/",
            {"passage_id": self.passage.id},
            format="json",
        )
        invalid_status = self.client.get("/api/practice-marks/?status=pending")

        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(duplicate.json()["id"], mark.id)
        self.assertEqual(duplicate.json()["note"], "Preserve my note")
        self.assertEqual(invalid_status.status_code, 400)
        self.assertEqual(invalid_status.json(), {
            "status": "Use 'unresolved' or 'resolved'."
        })

    def test_mock_users_have_separate_marks_for_the_same_passage(self):
        alex = self.client.post(
            "/api/practice-marks/", {"passage_id": self.passage.id}, format="json"
        )
        sam = self.client.post(
            "/api/practice-marks/",
            {"passage_id": self.passage.id, "note": "Sam practice plan"},
            format="json",
            HTTP_X_MOCK_USER="sam",
        )

        self.assertEqual(alex.status_code, 201)
        self.assertEqual(sam.status_code, 201)
        self.assertEqual(alex.json()["owner"], "alex")
        self.assertEqual(sam.json()["owner"], "sam")

        alex_marks = self.client.get("/api/practice-marks/")
        sam_marks = self.client.get("/api/practice-marks/", HTTP_X_MOCK_USER="sam")
        self.assertEqual([mark["owner"] for mark in alex_marks.json()], ["alex"])
        self.assertEqual([mark["owner"] for mark in sam_marks.json()], ["sam"])

    def test_practice_review_preserves_each_scores_context_and_resolves_a_mark(self):
        first_mark = PracticeMark.objects.create(passage=self.passage, note="Keep rhythm even")
        second_mark = PracticeMark.objects.create(passage=self.other_passage, note="Review opening")

        listing = self.client.get("/api/practice-marks/")
        self.assertEqual(listing.status_code, 200)
        marks = {item["id"]: item for item in listing.json()}
        self.assertEqual(marks[first_mark.id]["passage"]["score_id"], self.score.id)
        self.assertEqual(marks[first_mark.id]["passage"]["page_number"], 2)
        self.assertEqual(marks[second_mark.id]["passage"]["score_id"], self.other_score.id)
        self.assertEqual(marks[second_mark.id]["passage"]["movement"], "Movement II")

        update = self.client.patch(
            f"/api/practice-marks/{second_mark.id}/", {"is_resolved": True}, format="json"
        )
        self.assertEqual(update.status_code, 200)
        self.assertTrue(update.json()["is_resolved"])
        self.assertEqual(update.json()["note"], "Review opening")
        self.assertEqual(update.json()["passage"]["score_id"], self.other_score.id)

        unresolved = self.client.get("/api/practice-marks/?status=unresolved")
        self.assertEqual([item["id"] for item in unresolved.json()], [first_mark.id])

    def test_patch_updates_note_and_resolution_without_moving_passage(self):
        mark = PracticeMark.objects.create(passage=self.passage)
        response = self.client.patch(
            f"/api/practice-marks/{mark.id}/",
            {"note": "Review transition", "is_resolved": True},
            format="json",
        )
        move_attempt = self.client.patch(
            f"/api/practice-marks/{mark.id}/",
            {"passage_id": self.other_passage.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["note"], "Review transition")
        self.assertTrue(response.json()["is_resolved"])
        self.assertEqual(move_attempt.status_code, 400)
        self.assertIn("passage_id", move_attempt.json())
