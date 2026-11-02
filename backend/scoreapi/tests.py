from django.test import SimpleTestCase
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Passage, PracticeMark, Score


class HealthCheckTests(SimpleTestCase):
    def test_health_check_endpoint(self):
        response = self.client.get(reverse("scoreapi:health-check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "score-companion-api"})


class ScoreApiTests(APITestCase):
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

    def test_deleting_a_score_removes_its_passages_and_practice_marks(self):
        mark = PracticeMark.objects.create(passage=self.passage)
        response = self.client.delete(f"/api/scores/{self.score.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Score.objects.filter(pk=self.score.id).exists())
        self.assertFalse(Passage.objects.filter(pk=self.passage.id).exists())
        self.assertFalse(PracticeMark.objects.filter(pk=mark.id).exists())

    @override_settings(AUDIVERIS_COMMAND="/opt/audiveris")
    @patch("scoreapi.views.extract_pdf_measures", return_value=[("Page 1", 1, 1), ("Page 1", 2, 1), ("Page 2", 3, 2)])
    def test_pdf_extraction_replaces_passages_with_omr_result(self, extract_pdf):
        score = Score.objects.create(title="Scan", movement="Scan", instrument="Piano", page_count=1, available_offline=True, source_file=SimpleUploadedFile("scan.pdf", b"%PDF"))
        Passage.objects.create(score=score, section="Old", measure_number=1, page_number=1)
        response = self.client.post(f"/api/scores/{score.id}/extract-measures/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["passage_count"], 3)
        self.assertEqual(response.json()["page_count"], 2)
        self.assertEqual(Passage.objects.filter(score=score).count(), 3)
        extract_pdf.assert_called_once()

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

    def test_duplicate_mark_and_invalid_status_are_rejected(self):
        PracticeMark.objects.create(passage=self.passage)
        duplicate = self.client.post(
            "/api/practice-marks/",
            {"passage_id": self.passage.id},
            format="json",
        )
        invalid_status = self.client.get("/api/practice-marks/?status=pending")

        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("passage_id", duplicate.json())
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
