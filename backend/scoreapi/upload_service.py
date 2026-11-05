"""Store each uploaded file once and clean up files when database writes fail."""

import hashlib
import fcntl
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Count, Sum

from .models import Passage, Score


class UploadQuotaExceeded(ValueError):
    pass


@contextmanager
def upload_lock(owner):
    """Serialize public quota checks and file writes across our single-host workers."""
    if owner is None:
        yield
        return
    root = Path(settings.MEDIA_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".upload.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def enforce_upload_quota(owner, incoming_bytes):
    if owner is None:
        return
    for queryset, max_scores, max_bytes, message in [
        (Score.objects.filter(owner=owner), settings.PUBLIC_MAX_SCORES_PER_SESSION,
         settings.PUBLIC_MAX_BYTES_PER_SESSION, "Your browser library is full. Delete an uploaded score before adding another."),
        (Score.objects.filter(owner__isnull=False), settings.PUBLIC_MAX_SCORES_TOTAL,
         settings.PUBLIC_MAX_BYTES_TOTAL, "The demo storage limit has been reached. Please try later or contact the team."),
    ]:
        usage = queryset.aggregate(count=Count("id"), size=Sum("source_bytes"))
        if usage["count"] >= max_scores or (usage["size"] or 0) + incoming_bytes > max_bytes:
            raise UploadQuotaExceeded(message)


def file_digest(source):
    digest = hashlib.sha256()
    for chunk in source.chunks():
        digest.update(chunk)
    source.seek(0)
    return digest.hexdigest()


def store_upload(source, metadata, measures, owner=None):
    fingerprint = file_digest(source)
    with upload_lock(owner):
        return _store_upload(source, metadata, measures, owner, fingerprint)


def _store_upload(source, metadata, measures, owner, fingerprint):
    existing = Score.objects.filter(content_sha256=fingerprint, owner=owner).first()
    if existing:
        return existing, False

    enforce_upload_quota(owner, source.size)

    score = Score(**metadata, content_sha256=fingerprint, owner=owner, source_bytes=source.size,
                  extraction_state="complete" if measures else "not_started")
    # UUID file names isolate different uploads even when original names match.
    score.source_file.save(source.name, source, save=False)
    try:
        with transaction.atomic():
            score.save(force_insert=True)
            Passage.objects.bulk_create([
                Passage(score=score, section=section, measure_number=number, page_number=page)
                for section, number, page in measures
            ])
    except Exception as error:
        score.source_file.delete(save=False)
        if isinstance(error, IntegrityError):
            # Another request may have committed the same content first.
            existing = Score.objects.filter(content_sha256=fingerprint, owner=owner).first()
            if existing:
                return existing, False
        raise
    return score, True
