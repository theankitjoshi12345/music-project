from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from pathlib import Path
import re


def score_upload_path(instance, filename):
    owner = re.sub(r"[^a-zA-Z0-9_-]", "_", instance.owner or "local")[:64]
    identity = instance.content_sha256 or "unindexed"
    return f"scores/{owner}/{identity}{Path(filename).suffix.lower()}"


class Score(models.Model):
    """A downloaded musical part available to the score library."""

    title = models.CharField(max_length=200)
    movement = models.CharField(max_length=120)
    instrument = models.CharField(max_length=120)
    page_count = models.PositiveIntegerField()
    available_offline = models.BooleanField(default=True)
    source_file = models.FileField(upload_to=score_upload_path, blank=True)
    owner = models.CharField(max_length=64, null=True, blank=True, editable=False, db_index=True)
    source_bytes = models.PositiveBigIntegerField(default=0, editable=False)
    content_sha256 = models.CharField(max_length=64, null=True, blank=True, editable=False, db_index=True)
    passage_count = models.PositiveIntegerField(default=0, editable=False)
    extraction_state = models.CharField(max_length=20, default="not_started", choices=[
        ("not_started", "Not started"), ("processing", "Processing"),
        ("complete", "Complete"), ("failed", "Failed"),
    ])
    extraction_error = models.CharField(max_length=500, blank=True)
    extraction_updated_at = models.DateTimeField(null=True, blank=True)
    measure_layout_version = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["title", "movement", "instrument"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "content_sha256"], name="unique_owned_score_content"),
            models.UniqueConstraint(fields=["content_sha256"], condition=models.Q(owner__isnull=True),
                                    name="unique_legacy_score_content"),
        ]

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
    bounding_box = models.JSONField(null=True, blank=True)

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


class UsageCounter(models.Model):
    """Small persistent cost guard; one document per owner and action."""

    key = models.CharField(max_length=64, primary_key=True)
    owner = models.CharField(max_length=64, editable=False)
    action = models.CharField(max_length=32, editable=False)
    window_start = models.DateField()
    count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["owner", "action"], name="unique_usage_counter_action"),
        ]
