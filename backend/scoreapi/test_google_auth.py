"""Google identity verification and account isolation tests."""

import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import Score


@override_settings(
    DJANGO_AUTH_MODE="google",
    GOOGLE_OAUTH_CLIENT_ID="local-client.apps.googleusercontent.com",
    SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
)
class GoogleAuthenticationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        media = tempfile.TemporaryDirectory(prefix="google-auth-tests-")
        cls.addClassCleanup(media.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media.name)
        media_settings.enable()
        cls.addClassCleanup(media_settings.disable)

    def browser(self):
        client = APIClient(enforce_csrf_checks=True)
        session = client.get("/api/session/")
        self.assertEqual(session.status_code, 200)
        self.assertEqual(session.json()["auth_mode"], "google")
        self.assertFalse(session.json()["authenticated"])
        client.credentials(HTTP_X_CSRFTOKEN=session.json()["csrfToken"])
        return client

    def login(self, client, subject, email):
        identity = {"sub": subject, "email": email, "email_verified": True, "name": email.split("@")[0]}
        with patch("scoreapi.views.google_id_token.verify_oauth2_token", return_value=identity) as verify:
            response = client.post("/api/auth/google/", {"credential": "signed-google-token"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["authenticated"])
        self.assertEqual(response.json()["email"], email)
        self.assertNotContains(response, subject)
        verify.assert_called_once()
        return response

    def upload(self, client, content=b"%PDF-1.4 private google score"):
        return client.post("/api/scores/upload/", {
            "score_file": SimpleUploadedFile("account-score.pdf", content),
        }, format="multipart")

    def test_signed_out_browser_cannot_read_or_write_library(self):
        client = self.browser()
        self.assertEqual(client.get("/api/scores/").status_code, 403)
        self.assertEqual(self.upload(client).status_code, 403)

    def test_invalid_or_unverified_google_identity_is_rejected(self):
        client = self.browser()
        with patch("scoreapi.views.google_id_token.verify_oauth2_token", side_effect=ValueError):
            self.assertEqual(client.post("/api/auth/google/", {"credential": "bad"}, format="json").status_code, 401)
        with patch("scoreapi.views.google_id_token.verify_oauth2_token", return_value={
            "sub": "123", "email": "person@example.com", "email_verified": False,
        }):
            self.assertEqual(client.post("/api/auth/google/", {"credential": "unverified"}, format="json").status_code, 401)
        self.assertEqual(client.get("/api/scores/").status_code, 403)

    def test_two_google_accounts_are_isolated_and_owner_is_not_email(self):
        alice, bob = self.browser(), self.browser()
        self.login(alice, "google-subject-alice", "alice@example.com")
        self.login(bob, "google-subject-bob", "bob@example.com")
        uploaded = self.upload(alice)
        self.assertEqual(uploaded.status_code, 201)
        score = Score.objects.get(pk=uploaded.json()["id"])
        self.assertNotIn("alice", score.owner)
        self.assertEqual(len(score.owner), 64)
        self.assertEqual(bob.get("/api/scores/").json(), [])
        self.assertEqual(bob.get(f"/api/scores/{score.id}/").status_code, 404)
        self.assertEqual(alice.get(f"/api/scores/{score.id}/").status_code, 200)

    def test_logout_removes_access_but_same_google_account_recovers_library(self):
        client = self.browser()
        self.login(client, "returning-google-subject", "returning@example.com")
        uploaded = self.upload(client)
        self.assertEqual(uploaded.status_code, 201)
        self.assertEqual(client.post("/api/auth/logout/").status_code, 204)
        self.assertEqual(client.get("/api/scores/").status_code, 403)
        session = client.get("/api/session/")
        client.credentials(HTTP_X_CSRFTOKEN=session.json()["csrfToken"])
        self.login(client, "returning-google-subject", "new-address@example.com")
        self.assertEqual([item["id"] for item in client.get("/api/scores/").json()], [uploaded.json()["id"]])

    def test_login_and_logout_require_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        with patch("scoreapi.views.google_id_token.verify_oauth2_token") as verify:
            self.assertEqual(client.post("/api/auth/google/", {"credential": "token"}, format="json").status_code, 403)
            verify.assert_not_called()

    @override_settings(CLOUD_RUN_PUBLIC_URL="https://music-companion-api.example.run.app")
    def test_short_lived_extraction_ticket_preserves_owner_without_cookie(self):
        client = self.browser()
        self.login(client, "ticket-owner", "ticket@example.com")
        uploaded = self.upload(client)
        score_id = uploaded.json()["id"]
        ticket_response = client.post(f"/api/scores/{score_id}/extraction-ticket/")
        self.assertEqual(ticket_response.status_code, 200)
        ticket = ticket_response.json()
        self.assertEqual(
            ticket["url"],
            f"https://music-companion-api.example.run.app/api/scores/{score_id}/extract-measures/",
        )
        self.assertEqual(ticket_response["Cache-Control"], "private, no-store")

        direct = APIClient(enforce_csrf_checks=True)
        direct.credentials(HTTP_AUTHORIZATION=f"Bearer {ticket['token']}")
        with patch("scoreapi.views.extract_score_measures") as extract:
            response = direct.post(f"/api/scores/{score_id}/extract-measures/")
        self.assertEqual(response.status_code, 200)
        extract.assert_called_once_with(score_id)

        direct.credentials(HTTP_AUTHORIZATION=f"Bearer {ticket['token']}tampered")
        with patch("scoreapi.views.extract_score_measures") as extract:
            response = direct.post(f"/api/scores/{score_id}/extract-measures/")
        self.assertEqual(response.status_code, 403)
        extract.assert_not_called()

    @override_settings(CORS_ALLOWED_ORIGINS=["https://music-companion-513717.web.app"])
    def test_firebase_origin_can_preflight_only_the_direct_omr_request(self):
        response = APIClient().options(
            "/api/scores/1/extract-measures/",
            HTTP_ORIGIN="https://music-companion-513717.web.app",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], "https://music-companion-513717.web.app")
        self.assertIn("authorization", response["Access-Control-Allow-Headers"].lower())

