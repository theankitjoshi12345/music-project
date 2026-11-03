"""Store each uploaded file once and clean up files when database writes fail."""

import hashlib

from django.db import IntegrityError, transaction

from .models import Passage, Score


def file_digest(source):
    digest = hashlib.sha256()
    for chunk in source.chunks():
        digest.update(chunk)
    source.seek(0)
    return digest.hexdigest()


def store_upload(source, metadata, measures):
    fingerprint = file_digest(source)
    existing = Score.objects.filter(content_sha256=fingerprint).first()
    if existing:
        return existing, False

    score = Score(**metadata, content_sha256=fingerprint,
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
            existing = Score.objects.filter(content_sha256=fingerprint).first()
            if existing:
                return existing, False
        raise
    return score, True
