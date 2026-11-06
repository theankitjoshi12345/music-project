"""Bridge disposable app filesystems and persistent score object storage."""

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


@contextmanager
def local_file_path(field_file):
    """Yield a real path even when a FileField lives in Cloud Storage."""
    try:
        path = field_file.path
    except (AttributeError, NotImplementedError):
        path = None
    if path:
        yield path
        return

    suffix = Path(field_file.name).suffix.lower()
    with tempfile.TemporaryDirectory(prefix="score-companion-source-") as directory:
        destination = Path(directory) / f"source{suffix}"
        field_file.open("rb")
        try:
            with destination.open("wb") as output:
                shutil.copyfileobj(field_file.file, output)
        finally:
            field_file.close()
        yield str(destination)


def derived_asset_prefix(score):
    owner = re.sub(r"[^a-zA-Z0-9_-]", "_", score.owner or "local")[:64]
    identity = score.content_sha256 or f"score-{score.pk}"
    return f"derived/{owner}/{identity}/"


def derived_image_name(score, page_number, region):
    payload = json.dumps(region or {}, sort_keys=True, separators=(",", ":"))
    region_key = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"{derived_asset_prefix(score)}v{score.measure_layout_version}/page-{page_number}-{region_key}.png"


def load_cached_image(score, page_number, region):
    """Return a persistent derived image only in the GCS deployment."""
    if settings.FILE_STORAGE_BACKEND != "gcs":
        return None
    name = derived_image_name(score, page_number, region)
    if not default_storage.exists(name):
        return None
    with default_storage.open(name, "rb") as source:
        return source.read()


def save_cached_image(score, page_number, region, image):
    if settings.FILE_STORAGE_BACKEND != "gcs":
        return
    name = derived_image_name(score, page_number, region)
    if not default_storage.exists(name):
        default_storage.save(name, ContentFile(image, name=Path(name).name))


def delete_derived_assets(score):
    if settings.FILE_STORAGE_BACKEND != "gcs":
        return
    storage = default_storage
    if not hasattr(storage, "delete_prefix"):
        raise RuntimeError("The configured cloud storage cannot delete derived score assets safely.")
    storage.delete_prefix(derived_asset_prefix(score))
