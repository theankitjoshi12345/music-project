from django.db import models


class Score(models.Model):
    """A downloaded musical part available to the score library."""

    title = models.CharField(max_length=200)
    movement = models.CharField(max_length=120)
    instrument = models.CharField(max_length=120)
    page_count = models.PositiveIntegerField()
    available_offline = models.BooleanField(default=True)

    class Meta:
        ordering = ["title", "movement", "instrument"]

    def __str__(self):
        return f"{self.title} — {self.movement} ({self.instrument})"


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
    """A saved correction or practice reminder linked to exactly one passage."""

    passage = models.OneToOneField(
        Passage, on_delete=models.CASCADE, related_name="practice_mark"
    )
    note = models.CharField(max_length=500, blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["is_resolved", "-updated_at"]

    def __str__(self):
        return f"Practice mark: {self.passage}"
