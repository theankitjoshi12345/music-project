"""Exercise the real API against the local Firestore emulator."""

import os
import uuid
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from rest_framework.test import APIClient

from scoreapi.models import Passage, PracticeMark, Score
from scoreapi.persistence import delete_id_direct, delete_ids_direct


class Command(BaseCommand):
    help = "Run Google-auth account-isolation and CRUD smoke tests against the Firestore emulator."

    def _browser(self, subject, email):
        client = APIClient(enforce_csrf_checks=True)
        session = client.get("/api/session/")
        if session.status_code != 200:
            raise CommandError(f"Session endpoint returned {session.status_code}.")
        client.credentials(HTTP_X_CSRFTOKEN=session.json()["csrfToken"])
        identity = {"sub": subject, "email": email, "email_verified": True, "name": email.split("@")[0]}
        with patch("scoreapi.views.google_id_token.verify_oauth2_token", return_value=identity):
            response = client.post("/api/auth/google/", {"credential": "emulator-token"}, format="json")
        if response.status_code != 200:
            raise CommandError(f"Google session endpoint returned {response.status_code}.")
        return client

    def _cleanup(self, score_id):
        try:
            score = Score.objects.get(pk=score_id)
        except Score.DoesNotExist:
            return
        passage_ids = list(Passage.objects.filter(score_id=score_id).order_by().values_list("pk", flat=True))
        mark_ids = []
        for passage_id in passage_ids:
            mark_ids.extend(PracticeMark.objects.filter(passage_id=passage_id).order_by().values_list("pk", flat=True))
        delete_ids_direct(PracticeMark, mark_ids)
        delete_ids_direct(Passage, passage_ids)
        if score.source_file:
            score.source_file.delete(save=False)
        delete_id_direct(Score, score_id)

    def handle(self, *args, **options):
        if not os.environ.get("DATASTORE_EMULATOR_HOST"):
            raise CommandError("DATASTORE_EMULATOR_HOST is required; this command never targets production.")
        if settings.PERSISTENCE_BACKEND != "firestore" or settings.FILE_STORAGE_BACKEND != "filesystem":
            raise CommandError("Use Firestore persistence and filesystem storage for this emulator smoke test.")
        if settings.DJANGO_AUTH_MODE != "google":
            raise CommandError("Use DJANGO_AUTH_MODE=google for this smoke test.")

        run_id = uuid.uuid4().hex
        alice = self._browser(f"firestore-smoke-alice-{run_id}", f"alice-{run_id}@example.test")
        bob = self._browser(f"firestore-smoke-bob-{run_id}", f"bob-{run_id}@example.test")
        score_id = None
        try:
            upload = alice.post("/api/scores/upload/", {
                "score_file": SimpleUploadedFile("firestore-smoke.pdf", f"%PDF-1.4 {run_id}".encode()),
                "title": "Firestore emulator smoke test",
            }, format="multipart")
            if upload.status_code != 201:
                raise CommandError(f"Upload returned {upload.status_code}: {upload.content!r}")
            score_id = upload.json()["id"]

            alice_ids = [item["id"] for item in alice.get("/api/scores/").json()]
            if alice_ids != [score_id] or bob.get("/api/scores/").json() != []:
                raise CommandError("Google account score isolation failed.")
            if bob.get(f"/api/scores/{score_id}/").status_code != 404:
                raise CommandError("A second Google account could open the first account's score.")

            passage = alice.post(f"/api/scores/{score_id}/passages/", {
                "section": "Start", "measure_number": 1, "page_number": 1,
            }, format="json")
            if passage.status_code != 201:
                raise CommandError(f"Passage creation returned {passage.status_code}.")
            passage_id = passage.json()["id"]
            mark = alice.post("/api/practice-marks/", {
                "passage_id": passage_id, "note": "Firestore emulator test",
            }, format="json")
            if mark.status_code != 201:
                raise CommandError(f"Practice mark creation returned {mark.status_code}.")
            mark_id = mark.json()["id"]
            if alice.delete(f"/api/practice-marks/{mark_id}/").status_code != 204:
                raise CommandError("Practice mark deletion failed.")
            if PracticeMark.objects.filter(pk=mark_id).exists():
                raise CommandError("Practice mark data leaked after deletion.")

            if alice.delete(f"/api/scores/{score_id}/").status_code != 204:
                raise CommandError("Score deletion failed.")
            if Score.objects.filter(pk=score_id).exists() or Passage.objects.filter(pk=passage_id).exists():
                raise CommandError("Score or passage data leaked after deletion.")
            score_id = None
        finally:
            if score_id is not None:
                self._cleanup(score_id)

        self.stdout.write(self.style.SUCCESS("Firestore emulator API lifecycle passed."))
