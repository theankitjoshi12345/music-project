"""Store each uploaded file once and clean up files when database writes fail."""

import hashlib
import fcntl
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings
from django.db import IntegrityError, transaction

from .models import Passage, Score
from .persistence import delete_id_direct, delete_ids_direct


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
        # Fetch full entities instead of a Datastore projection query, which
        # would require an otherwise unnecessary index on the size field.
        stored_sizes = [score.source_bytes for score in queryset.order_by()]
        if len(stored_sizes) >= max_scores or sum(stored_sizes) + incoming_bytes > max_bytes:
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
    # Clear Score.Meta.ordering. Otherwise Datastore expands this equality
    # lookup into an unnecessary five-property composite index.
    existing = Score.objects.filter(content_sha256=fingerprint, owner=owner).order_by().first()
    if existing:
        return existing, False

    enforce_upload_quota(owner, source.size)

    score = Score(**metadata, content_sha256=fingerprint, owner=owner, source_bytes=source.size,
                  passage_count=len(measures),
                  extraction_state="complete" if measures else "not_started")
    # The upload path is owner-scoped and content-addressed.
    score.source_file.save(source.name, source, save=False)
    score_saved = False
    try:
        score.save(force_insert=True)
        score_saved = True
        # Keep invalid MusicXML measure sets inside a savepoint so an integrity
        # failure can be cleaned up on SQLite. This is one Firestore bulk write,
        # not a query-after-write transaction.
        with transaction.atomic():
            Passage.objects.bulk_create([
                Passage(score=score, section=section, measure_number=number, page_number=page)
                for section, number, page in measures
            ])
    except Exception as error:
        if isinstance(error, IntegrityError) and not score_saved:
            # Another request may have committed the same content first.
            existing = Score.objects.filter(content_sha256=fingerprint, owner=owner).order_by().first()
            if existing:
                if score.source_file.name != existing.source_file.name:
                    score.source_file.delete(save=False)
                return existing, False
        if score.pk:
            passage_ids = list(Passage.objects.filter(score_id=score.pk).order_by().values_list("pk", flat=True))
            if passage_ids:
                delete_ids_direct(Passage, passage_ids)
            delete_id_direct(Score, score.pk)
        # A concurrent identical upload can share the content-addressed object.
        # Remove it only after rolling back our rows and confirming that no
        # committed score still references this storage name.
        if not Score.objects.filter(source_file=score.source_file.name).exists():
            score.source_file.delete(save=False)
        raise
    return score, True
