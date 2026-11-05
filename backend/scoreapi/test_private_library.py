"""Exercise the authorization boundary with real cookies and CSRF checks."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient

from .models import Passage, PracticeMark, Score


@override_settings(DJANGO_AUTH_MODE="session")
class PrivateLibraryTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        media = tempfile.TemporaryDirectory(prefix="private-library-tests-")
        cls.addClassCleanup(media.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media.name)
        media_settings.enable()
        cls.addClassCleanup(media_settings.disable)

    def new_browser(self):
        browser = APIClient(enforce_csrf_checks=True)
        response = browser.get("/api/session/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["auth_mode"], "session")
        browser.credentials(HTTP_X_CSRFTOKEN=response.json()["csrfToken"])
        return browser

    def upload(self, browser, content=b"%PDF-1.4 private score"):
        return browser.post("/api/scores/upload/", {
            "score_file": SimpleUploadedFile("private.pdf", content),
        }, format="multipart")

    def setUp(self):
        self.alice = self.new_browser()
        self.bob = self.new_browser()
        response = self.upload(self.alice)
        self.assertEqual(response.status_code, 201)
        self.score = Score.objects.get(pk=response.json()["id"])
        self.passage = Passage.objects.create(score=self.score, section="A", measure_number=1,
                                              page_number=1, bounding_box={"x": 0, "y": 0, "width": 1, "height": 1})
        self.mark = PracticeMark.objects.create(passage=self.passage, owner=self.score.owner, note="Private reminder")

    def test_missing_session_cannot_read_library_or_start_work(self):
        browser = APIClient()
        self.assertEqual(browser.get("/api/scores/").status_code, 403)
        self.assertEqual(browser.get(f"/api/scores/{self.score.id}/file/").status_code, 403)
        self.assertEqual(browser.post(f"/api/scores/{self.score.id}/extract-measures/").status_code, 403)

    @patch("scoreapi.views.render_pdf", return_value=b"PNG")
    @patch("scoreapi.views.extract_score_measures")
    def test_second_browser_cannot_read_change_or_render_first_browsers_data(self, extract, render):
        self.assertEqual(self.bob.get("/api/scores/").json(), [])
        self.assertEqual(self.bob.get("/api/practice-marks/").json(), [])
        for path in [f"/api/scores/{self.score.id}/", f"/api/scores/{self.score.id}/file/",
                     f"/api/scores/{self.score.id}/passages/", f"/api/scores/{self.score.id}/pages/1/image/",
                     f"/api/passages/{self.passage.id}/preview/"]:
            self.assertEqual(self.bob.get(path).status_code, 404, path)
        self.assertEqual(self.bob.delete(f"/api/scores/{self.score.id}/").status_code, 404)
        self.assertEqual(self.bob.post(f"/api/scores/{self.score.id}/extract-measures/").status_code, 404)
        self.assertEqual(self.bob.post(f"/api/scores/{self.score.id}/passages/", {
            "section": "A", "measure_number": 2, "page_number": 1,
        }, format="json").status_code, 404)
        self.assertEqual(self.bob.post("/api/practice-marks/", {"passage_id": self.passage.id}, format="json").status_code, 400)
        self.assertEqual(self.bob.patch(f"/api/practice-marks/{self.mark.id}/", {"note": "Changed"}, format="json").status_code, 404)
        self.assertEqual(self.bob.delete(f"/api/practice-marks/{self.mark.id}/").status_code, 404)
        extract.assert_not_called()
        render.assert_not_called()
        self.mark.refresh_from_db()
        self.assertEqual(self.mark.note, "Private reminder")

    def test_mock_header_and_json_owner_cannot_impersonate_another_browser(self):
        self.assertEqual(self.bob.get("/api/scores/", HTTP_X_MOCK_USER=self.score.owner).json(), [])
        response = self.bob.post("/api/practice-marks/", {
            "passage_id": self.passage.id, "owner": self.score.owner,
        }, format="json", HTTP_X_MOCK_USER=self.score.owner)
        self.assertEqual(response.status_code, 400)

    def test_deduplication_is_private_per_browser_and_deletion_keeps_other_copy(self):
        repeated = self.upload(self.alice)
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(repeated.json()["id"], self.score.id)
        separate = self.upload(self.bob)
        self.assertEqual(separate.status_code, 201)
        other = Score.objects.get(pk=separate.json()["id"])
        self.assertNotEqual(other.id, self.score.id)
        self.assertNotEqual(other.source_file.name, self.score.source_file.name)
        self.assertEqual(self.alice.delete(f"/api/scores/{self.score.id}/").status_code, 204)
        self.assertFalse(Path(settings.MEDIA_ROOT, self.score.source_file.name).exists())
        self.assertTrue(Path(other.source_file.path).exists())
        self.assertFalse(PracticeMark.objects.filter(pk=self.mark.id).exists())

    def test_legacy_unowned_data_is_never_in_a_public_browser_library(self):
        legacy = Score.objects.create(title="Legacy private score", movement="Old", instrument="Piano", page_count=1)
        self.assertNotIn(legacy.id, [score["id"] for score in self.alice.get("/api/scores/").json()])
        self.assertEqual(self.alice.get(f"/api/scores/{legacy.id}/").status_code, 404)
        with override_settings(DJANGO_AUTH_MODE="demo"):
            self.assertEqual([score["id"] for score in self.alice.get("/api/scores/").json()], [legacy.id])

    def test_csrf_required_even_for_anonymous_session_writes(self):
        self.alice.credentials()
        self.assertEqual(self.alice.delete(f"/api/scores/{self.score.id}/").status_code, 403)
        self.assertEqual(self.upload(self.alice).status_code, 403)
        token = self.alice.get("/api/session/").json()["csrfToken"]
        self.alice.credentials(HTTP_X_CSRFTOKEN=token)
        self.assertEqual(self.alice.delete(f"/api/scores/{self.score.id}/", HTTP_ORIGIN="https://attacker.example").status_code, 403)
        self.assertTrue(Score.objects.filter(pk=self.score.id).exists())

    def test_original_file_is_authorized_inline_pdf_and_does_not_expose_storage_path(self):
        detail = self.alice.get(f"/api/scores/{self.score.id}/").json()
        self.assertEqual(detail["source_type"], "pdf")
        self.assertEqual(detail["source_file"], f"/api/scores/{self.score.id}/file/")
        response = self.alice.get(detail["source_file"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(response["X-Frame-Options"], "SAMEORIGIN")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(b"".join(response.streaming_content), b"%PDF-1.4 private score")
        response.close()

    def test_existing_cookie_keeps_library_after_session_reinitialization(self):
        old_owner = self.alice.session["score_owner"]
        response = self.alice.get("/api/session/")
        self.assertNotIn(old_owner, response.content.decode())
        self.assertEqual(self.alice.session["score_owner"], old_owner)
        self.assertEqual([score["id"] for score in self.alice.get("/api/scores/").json()], [self.score.id])
        self.assertTrue(response.cookies["csrftoken"]["samesite"])

    def test_library_requests_refresh_the_thirty_day_inactivity_expiry(self):
        key = self.alice.cookies[settings.SESSION_COOKIE_NAME].value
        Session.objects.filter(session_key=key).update(expire_date=timezone.now() + timedelta(days=1))
        self.assertEqual(self.alice.get("/api/scores/").status_code, 200)
        self.assertGreater(Session.objects.get(session_key=key).expire_date, timezone.now() + timedelta(days=29))

    @override_settings(PUBLIC_MAX_SCORES_PER_SESSION=1)
    def test_session_upload_quota_rejects_new_file_but_allows_duplicate(self):
        before = set(Path(settings.MEDIA_ROOT).rglob("*"))
        self.assertEqual(self.upload(self.alice).status_code, 200)
        rejected = self.upload(self.alice, b"%PDF-1.4 second score")
        self.assertEqual(rejected.status_code, 429)
        self.assertIn("Delete", rejected.json()["detail"])
        self.assertEqual(set(Path(settings.MEDIA_ROOT).rglob("*")), before)

    @override_settings(PUBLIC_MAX_SCORES_TOTAL=1)
    def test_global_quota_is_shared_by_separate_sessions(self):
        self.assertEqual(self.upload(self.bob).status_code, 429)
        self.assertEqual(Score.objects.filter(owner__isnull=False).count(), 1)

    @override_settings(PUBLIC_MAX_BYTES_PER_SESSION=25)
    def test_byte_quota_is_enforced_before_saving_any_extra_file(self):
        self.assertEqual(self.upload(self.alice, b"%PDF-1.4 extra" * 10).status_code, 429)
        self.assertEqual(Score.objects.filter(owner=self.score.owner).count(), 1)
