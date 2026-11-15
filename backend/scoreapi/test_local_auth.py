"""Local accounts are the default self-contained development sign-in path."""

import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import LocalAccount


@override_settings(DJANGO_AUTH_MODE="local")
class LocalAccountTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        media = tempfile.TemporaryDirectory(prefix="local-account-tests-")
        cls.addClassCleanup(media.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media.name)
        media_settings.enable()
        cls.addClassCleanup(media_settings.disable)

    def browser(self):
        client = APIClient(enforce_csrf_checks=True)
        response = client.get("/api/session/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["authenticated"])
        self.assertEqual(response.json()["auth_mode"], "local")
        client.credentials(HTTP_X_CSRFTOKEN=response.json()["csrfToken"])
        return client

    def register(self, client, username, password="long-private-password"):
        return client.post("/api/auth/register/", {"username": username, "password": password}, format="json")

    def test_register_login_logout_and_private_library(self):
        alice, bob = self.browser(), self.browser()
        self.assertEqual(self.register(alice, "alice").status_code, 200)
        self.assertEqual(LocalAccount.objects.count(), 1)
        upload = alice.post("/api/scores/upload/", {
            "score_file": SimpleUploadedFile("alice.pdf", b"%PDF-1.4 local account score"),
        }, format="multipart", HTTP_X_MOCK_USER="bob")
        self.assertEqual(upload.status_code, 201)
        self.assertEqual(len(alice.get("/api/scores/").json()), 1)
        self.assertEqual(self.register(bob, "bob").status_code, 200)
        self.assertEqual(bob.get("/api/scores/").json(), [])
        self.assertEqual(alice.post("/api/auth/logout/").status_code, 204)
        self.assertEqual(alice.get("/api/scores/").status_code, 403)
        self.assertEqual(alice.get("/api/session/").status_code, 200)
        login = alice.post("/api/auth/login/", {"username": "alice", "password": "long-private-password"}, format="json")
        self.assertEqual(login.status_code, 200)
        self.assertEqual(len(alice.get("/api/scores/").json()), 1)

    def test_registration_rejects_duplicate_user_and_weak_password(self):
        browser = self.browser()
        self.assertEqual(self.register(browser, "musician").status_code, 200)
        second = self.browser()
        self.assertEqual(self.register(second, "musician").status_code, 400)
        weak = self.browser().post("/api/auth/register/", {"username": "new-user", "password": "short"}, format="json")
        self.assertEqual(weak.status_code, 400)
