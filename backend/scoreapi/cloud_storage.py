"""Private Google Cloud Storage with create-only writes and guarded deletes."""

import mimetypes

from google.api_core.exceptions import PreconditionFailed
from google.cloud.storage.retry import DEFAULT_RETRY
from storages.backends.gcloud import GoogleCloudStorage
from storages.utils import clean_name


class ConflictSafeGoogleCloudStorage(GoogleCloudStorage):
    """Avoid silently overwriting or deleting a concurrently replaced object.

    Score source names are content-addressed. Two identical requests may safely
    converge on the same object, while generation preconditions protect against
    accidental replacement and stale deletes.
    """

    def _save(self, name, content):
        cleaned_name = clean_name(name)
        normalized_name = self._normalize_name(cleaned_name)
        content.name = cleaned_name
        content_type, content_encoding = mimetypes.guess_type(cleaned_name)
        parameters = self.get_object_parameters(normalized_name)
        if content_encoding and "content_encoding" not in parameters:
            parameters["content_encoding"] = content_encoding

        blob = self.bucket.blob(normalized_name, chunk_size=self.blob_chunk_size)
        for property_name, value in parameters.items():
            if property_name not in {"acl", "content_type"}:
                setattr(blob, property_name, value)
        try:
            blob.upload_from_file(
                content,
                rewind=True,
                size=getattr(content, "size", None),
                content_type=parameters.get("content_type", content_type),
                predefined_acl=parameters.get("acl", self.default_acl),
                if_generation_match=0,
                checksum="crc32c",
                retry=DEFAULT_RETRY,
            )
        except PreconditionFailed:
            # A concurrent request already created this content-addressed name.
            # Never replace it; the database uniqueness check selects the owner.
            if not self.bucket.get_blob(normalized_name):
                raise
        return cleaned_name

    def delete(self, name):
        normalized_name = self._normalize_name(clean_name(name))
        blob = self.bucket.get_blob(normalized_name)
        if not blob:
            return
        # If an object changed after this read, leave the new generation intact.
        blob.delete(if_generation_match=blob.generation, retry=DEFAULT_RETRY)

    def delete_prefix(self, prefix):
        """Delete a private derived-asset tree without stale-generation races."""
        normalized_prefix = self._normalize_name(clean_name(prefix))
        for blob in self.bucket.list_blobs(prefix=normalized_prefix):
            blob.delete(if_generation_match=blob.generation, retry=DEFAULT_RETRY)
