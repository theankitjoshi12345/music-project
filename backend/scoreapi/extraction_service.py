"""Coordinate local OMR and commit imported measures without losing marks."""

from datetime import timedelta
import logging
import fcntl
from contextlib import contextmanager
from pathlib import Path
import subprocess

from django.conf import settings
from django.utils import timezone

from .models import Passage, Score
from .score_extract import OMRUnavailable, extract_pdf_measures
from .storage_assets import local_file_path

logger = logging.getLogger(__name__)


class ExtractionBusy(RuntimeError):
    pass


@contextmanager
def recognition_slot():
    """One Java recognition process across all workers on this persistent host.

    flock is released by the OS on a crash; no stale lock files need deleting.
    Local development and Linux production both support flock.
    """
    lock_path = Path(settings.DATA_DIR) / ".recognition.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ExtractionBusy("Another score is being converted. Please retry in a moment.")
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def extract_score_measures(score_id):
    # Acquire before marking a score processing. Refused requests remain retryable.
    with recognition_slot():
        return _extract_score_measures(score_id)


def _extract_score_measures(score_id):
    score = Score.objects.get(pk=score_id)
    if score.extraction_state == "complete" and score.measure_layout_version >= 1:
        return score

    now = timezone.now()
    stale_before = now - timedelta(seconds=settings.OMR_TIMEOUT_SECONDS + 90)
    # recognition_slot serializes every OMR process on the single Cloud Run
    # instance. A crashed request remains retryable after its lease expires.
    if score.extraction_state == "processing" and score.extraction_updated_at and score.extraction_updated_at > stale_before:
        raise ExtractionBusy("Measures are already being extracted for this score.")
    score.extraction_state = "processing"
    score.extraction_error = ""
    score.extraction_updated_at = now
    score.save(update_fields=["extraction_state", "extraction_error", "extraction_updated_at"])

    try:
        def record_page_count(page_count):
            # Publish the real page count early without resetting the start time.
            if not Score.objects.filter(pk=score_id).update(page_count=page_count):
                raise Score.DoesNotExist

        with local_file_path(score.source_file) as source_path:
            result = extract_pdf_measures(source_path, settings.AUDIVERIS_COMMAND,
                                          timeout=settings.OMR_TIMEOUT_SECONDS, max_pages=settings.OMR_MAX_PAGES,
                                          on_page_count=record_page_count)

        # Avoid collection queries after writes in a Firestore transaction.
        # Partial imports are safe: completion is published only after every
        # measure is saved, and retries reuse passage IDs and practice marks.
        existing = {
            (passage.section, passage.measure_number): passage
            for passage in Passage.objects.filter(score_id=score_id).order_by()
        }
        for section, number, page in result.measures:
            passage = existing.get((section, number))
            if passage is None:
                passage = Passage(score_id=score_id, section=section, measure_number=number)
            passage.page_number = page
            passage.bounding_box = result.regions.get((section, number, page))
            passage.save()
            existing[(section, number)] = passage

        final_score = Score.objects.get(pk=score_id)
        final_score.page_count = result.page_count
        final_score.passage_count = len(existing)
        final_score.extraction_state = "complete"
        final_score.extraction_error = ""
        final_score.extraction_updated_at = timezone.now()
        final_score.measure_layout_version = 1 if result.regions else 0
        final_score.save(update_fields=[
            "page_count", "passage_count", "extraction_state", "extraction_error",
            "extraction_updated_at", "measure_layout_version",
        ])
    except Score.DoesNotExist:
        raise
    except (OMRUnavailable, subprocess.SubprocessError, OSError, ValueError) as error:
        logger.warning("Score %s extraction failed: %s", score_id, error)
        if isinstance(error, subprocess.TimeoutExpired):
            message = "Extraction took too long. Try a shorter PDF and retry."
        elif isinstance(error, subprocess.CalledProcessError):
            message = "The score could not be recognized. Try a clear, unencrypted sheet-music PDF."
        elif isinstance(error, OSError):
            message = "The local recognition tool or PDF could not be opened. Check the server setup and retry."
        else:
            message = str(error)
        Score.objects.filter(pk=score_id).update(
            extraction_state="failed", extraction_error=message[:500], extraction_updated_at=timezone.now(),
        )
        if isinstance(error, OMRUnavailable):
            raise OMRUnavailable(message) from error
        raise ValueError(message) from error
    return Score.objects.get(pk=score_id)
