from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction

from scoreapi.models import Score
from scoreapi.upload_service import file_digest


class Command(BaseCommand):
    help = "Index existing uploaded files for duplicate detection; never delete score data."

    def handle(self, *args, **options):
        indexed = 0
        for score in Score.objects.filter(content_sha256__isnull=True).exclude(source_file=""):
            try:
                with score.source_file.open("rb") as source:
                    digest = file_digest(source)
                with transaction.atomic():
                    Score.objects.filter(pk=score.pk, content_sha256__isnull=True).update(content_sha256=digest)
                indexed += 1
            except (OSError, IntegrityError):
                self.stderr.write(f"Skipped score {score.pk}: file missing or content already indexed.")
        self.stdout.write(f"Indexed {indexed} existing uploads.")
