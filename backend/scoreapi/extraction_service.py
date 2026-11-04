"""Coordinate local OMR and commit imported measures without losing marks."""

from datetime import timedelta
import logging
import subprocess

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Passage, Score
from .score_extract import OMRUnavailable, extract_pdf_measures

logger = logging.getLogger(__name__)


class ExtractionBusy(RuntimeError):
    pass


def extract_score_measures(score_id):
    score = Score.objects.get(pk=score_id)
    if score.extraction_state == "complete" and score.measure_layout_version >= 1:
        return score

    now = timezone.now()
    stale_before = now - timedelta(seconds=settings.OMR_TIMEOUT_SECONDS + 90)
    # A conditional UPDATE is atomic on SQLite too. A second tab cannot launch
    # a second OMR job for this score. Crashed requests can retry after expiry.
    claimed = Score.objects.filter(pk=score_id).exclude(extraction_state="complete", measure_layout_version__gte=1).exclude(
        extraction_state="processing", extraction_updated_at__gt=stale_before,
    ).update(extraction_state="processing", extraction_error="", extraction_updated_at=now)
    if not claimed:
        latest = Score.objects.get(pk=score_id)
        if latest.extraction_state == "complete" and latest.measure_layout_version >= 1:
            return latest
        raise ExtractionBusy("Measures are already being extracted for this score.")

    try:
        def record_page_count(page_count):
            # Publish the real page count early without resetting the start time.
            if not Score.objects.filter(pk=score_id).update(page_count=page_count):
                raise Score.DoesNotExist

        result = extract_pdf_measures(score.source_file.path, settings.AUDIVERIS_COMMAND,
                                      timeout=settings.OMR_TIMEOUT_SECONDS, max_pages=settings.OMR_MAX_PAGES,
                                      on_page_count=record_page_count)
        with transaction.atomic():
            if not Score.objects.filter(pk=score_id).update(extraction_updated_at=timezone.now()):
                raise Score.DoesNotExist
            for section, number, page in result.measures:
                # Preserve passage IDs and attached notes on retry/import.
                Passage.objects.update_or_create(
                    score_id=score_id, section=section, measure_number=number,
                    defaults={"page_number": page, "bounding_box": result.regions.get((section, number, page))},
                )
            Score.objects.filter(pk=score_id).update(
                page_count=result.page_count, extraction_state="complete",
                extraction_error="", extraction_updated_at=timezone.now(),
                measure_layout_version=1 if result.regions else 0,
            )
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
