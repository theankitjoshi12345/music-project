from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Score(models.Model):
    """A downloaded musical part available to the score library."""

    title = models.CharField(max_length=200)
    movement = models.CharField(max_length=120)
    instrument = models.CharField(max_length=120)
    page_count = models.PositiveIntegerField()
    available_offline = models.BooleanField(default=True)
    source_file = models.FileField(upload_to="scores/", blank=True)
    extraction_state = models.CharField(max_length=20, default="not_started", choices=[
        ("not_started", "Not started"), ("processing", "Processing"),
        ("complete", "Complete"), ("failed", "Failed"),
    ])
    extraction_error = models.CharField(max_length=500, blank=True)
    extraction_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["title", "movement", "instrument"]

    def __str__(self):
        return f"{self.title} — {self.movement} ({self.instrument})"

    @property
    def extraction_expired(self):
        return self.extraction_state == "processing" and (
            self.extraction_updated_at is None or self.extraction_updated_at <
            timezone.now() - timedelta(seconds=settings.OMR_TIMEOUT_SECONDS + 90)
        )


class Passage(models.Model):
    """A measure within a score that can be marked for focused practice."""

    score = models.ForeignKey(Score, on_delete=models.CASCADE, related_name="passages")
    section = models.CharField(max_length=80)
    measure_number = models.PositiveIntegerField()
    page_number = models.PositiveIntegerField()

    class Meta:
        ordering = ["page_number", "section", "measure_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["score", "section", "measure_number"],
                name="unique_measure_per_score_section",
            )
        ]

    def __str__(self):
        return f"{self.score}: {self.section}, m. {self.measure_number}"


class PracticeMark(models.Model):
    """A mock-user-scoped correction or practice reminder for one passage."""

    owner = models.CharField(max_length=64, default="alex")
    passage = models.ForeignKey(
        Passage, on_delete=models.CASCADE, related_name="practice_marks"
    )
    note = models.CharField(max_length=500, blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["is_resolved", "-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["passage", "owner"], name="unique_mark_per_passage_owner"
            )
        ]

    def __str__(self):
        return f"Practice mark: {self.passage}"
