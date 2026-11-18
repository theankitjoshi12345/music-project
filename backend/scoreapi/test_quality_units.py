"""Focused P12 unit and integration coverage for business rules."""

from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from .models import Passage, PracticeMark, Score, UsageCounter, score_upload_path
from .serializers import PassageCreateSerializer, PracticeMarkSerializer, ScoreSerializer
from .usage import UsageLimitExceeded, consume_omr_allowance


class UsageAllowanceTests(TestCase):
    """Recognition limits must persist, reset daily, and never over-count."""

    @override_settings(OMR_DAILY_LIMIT=2)
    def test_allowance_counts_per_owner_and_rejects_the_next_request(self):
        consume_omr_allowance("alice")
        consume_omr_allowance("alice")

        counter = UsageCounter.objects.get(owner="alice", action="omr")
        self.assertEqual(counter.count, 2)
        with self.assertRaisesRegex(UsageLimitExceeded, r"Daily PDF recognition limit reached \(2\)"):
            consume_omr_allowance("alice")

        consume_omr_allowance("bob")
        self.assertEqual(UsageCounter.objects.get(owner="bob", action="omr").count, 1)

    @override_settings(OMR_DAILY_LIMIT=1)
    def test_allowance_resets_only_when_the_local_day_changes(self):
        with patch("scoreapi.usage.timezone.localdate", return_value=date(2026, 11, 16)):
            consume_omr_allowance("alice")

        with patch("scoreapi.usage.timezone.localdate", return_value=date(2026, 11, 17)):
            consume_omr_allowance("alice")

        counter = UsageCounter.objects.get(owner="alice", action="omr")
        self.assertEqual(counter.window_start, date(2026, 11, 17))
        self.assertEqual(counter.count, 1)

    @override_settings(OMR_DAILY_LIMIT=0)
    def test_disabled_allowance_fails_before_creating_a_counter(self):
        with self.assertRaisesRegex(UsageLimitExceeded, "temporarily unavailable"):
            consume_omr_allowance("alice")
        self.assertFalse(UsageCounter.objects.exists())


class SerializerBusinessRuleTests(TestCase):
    def setUp(self):
        self.score = Score.objects.create(
            title="Etude", movement="Practice", instrument="Piano", page_count=2,
            owner="owner-a", extraction_state="processing",
        )
        self.passage = Passage.objects.create(
            score=self.score, section="A", measure_number=1, page_number=1,
        )
        self.mark = PracticeMark.objects.create(
            passage=self.passage, owner="owner-a", note="Initial note",
        )

    def test_passage_serializer_normalizes_section_and_rejects_invalid_score_bounds(self):
        valid = PassageCreateSerializer(
            data={"section": "  A  ", "measure_number": 2, "page_number": 2},
            context={"score": self.score},
        )
        self.assertTrue(valid.is_valid(), valid.errors)
        self.assertEqual(valid.validated_data["section"], "A")

        blank_section = PassageCreateSerializer(
            data={"section": "   ", "measure_number": 2, "page_number": 2},
            context={"score": self.score},
        )
        self.assertFalse(blank_section.is_valid())
        self.assertIn("section", blank_section.errors)

        page_outside_score = PassageCreateSerializer(
            data={"section": "A", "measure_number": 2, "page_number": 3},
            context={"score": self.score},
        )
        self.assertFalse(page_outside_score.is_valid())
        self.assertIn("page_number", page_outside_score.errors)

        zero_measure = PassageCreateSerializer(
            data={"section": "A", "measure_number": 0, "page_number": 1},
            context={"score": self.score},
        )
        self.assertFalse(zero_measure.is_valid())
        self.assertIn("measure_number", zero_measure.errors)

    def test_practice_mark_trims_note_and_cannot_be_retargeted(self):
        update = PracticeMarkSerializer(self.mark, data={"note": "  Shape the ending  "}, partial=True)
        self.assertTrue(update.is_valid(), update.errors)
        self.assertEqual(update.validated_data["note"], "Shape the ending")

        other = Passage.objects.create(score=self.score, section="A", measure_number=2, page_number=1)
        move = PracticeMarkSerializer(self.mark, data={"passage_id": other.pk}, partial=True)
        self.assertFalse(move.is_valid())
        self.assertIn("passage_id", move.errors)

    @override_settings(OMR_TIMEOUT_SECONDS=120, OMR_ESTIMATED_SECONDS_PER_PAGE=20)
    def test_score_serializer_marks_stale_work_failed_and_bounds_the_estimate(self):
        self.score.extraction_updated_at = self.score.extraction_updated_at - timedelta(seconds=211) if self.score.extraction_updated_at else None
        # A processing record with no heartbeat is stale by design.
        data = ScoreSerializer(self.score).data
        self.assertEqual(data["extraction_status"], "failed")
        self.assertIn("interrupted", data["extraction_error"])
        self.assertIsNone(data["extraction_started_at"])
        self.assertIsNone(data["extraction_estimated_seconds"])

        self.score.source_file.name = "scores/owner-a/etude.pdf"
        self.score.page_count = 20
        self.score.extraction_state = "not_started"
        self.score.extraction_updated_at = None
        data = ScoreSerializer(self.score).data
        self.assertEqual(data["extraction_estimated_seconds"], 120)

    def test_score_upload_path_keeps_storage_names_owner_scoped_and_safe(self):
        self.score.owner = "google:player@example.com"
        self.score.content_sha256 = "abc123"
        self.assertEqual(score_upload_path(self.score, "My Score.PDF"), "scores/google_player_example_com/abc123.pdf")
