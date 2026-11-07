"""Production configuration invariants that are easy to break locally."""

import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase


class ProductionSettingsTests(SimpleTestCase):
    def test_firebase_rewrite_uses_the_only_forwarded_session_cookie(self):
        backend = Path(__file__).resolve().parents[1]
        environment = {
            **os.environ,
            "DJANGO_ENV": "production",
            "DJANGO_DEBUG": "false",
            "DJANGO_AUTH_MODE": "google",
            "DJANGO_SECRET_KEY": "production-test-secret-" + ("x" * 64),
            "DJANGO_ALLOWED_HOSTS": "ci.example.test",
            "GOOGLE_OAUTH_CLIENT_ID": "ci-client.apps.googleusercontent.com",
        }
        result = subprocess.run(
            [sys.executable, "-c", "from config import settings; print(settings.SESSION_COOKIE_NAME)"],
            cwd=backend,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stdout.strip(), "__session")
