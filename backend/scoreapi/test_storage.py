"""Object-storage safety and disposable-filesystem compatibility tests."""

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

from django.core.files.base import ContentFile
from django.test import SimpleTestCase
from google.api_core.exceptions import PreconditionFailed

from .cloud_storage import ConflictSafeGoogleCloudStorage
from .storage_assets import local_file_path


class RemoteFieldFile:
    name = "scores/private/source.pdf"

    @property
    def path(self):
        raise NotImplementedError

    def open(self, mode):
        self.file = BytesIO(b"persistent cloud bytes")

    def close(self):
        self.file.close()


class StorageAssetTests(SimpleTestCase):
    def test_remote_source_is_materialized_only_for_the_tool_call(self):
        source = RemoteFieldFile()
        with local_file_path(source) as path:
            materialized = Path(path)
            self.assertEqual(materialized.suffix, ".pdf")
            self.assertEqual(materialized.read_bytes(), b"persistent cloud bytes")
        self.assertFalse(materialized.exists())

    def storage_with_bucket(self):
        storage = ConflictSafeGoogleCloudStorage(bucket_name="test-bucket", project_id="test-project")
        bucket = MagicMock()
        bucket.name = "test-bucket"
        return storage, bucket

    def test_cloud_save_uses_create_only_generation_and_crc32c(self):
        storage, bucket = self.storage_with_bucket()
        blob = bucket.blob.return_value
        with patch.object(ConflictSafeGoogleCloudStorage, "bucket", new_callable=PropertyMock, return_value=bucket):
            name = storage._save("scores/owner/hash.pdf", ContentFile(b"score", name="score.pdf"))
        self.assertEqual(name, "scores/owner/hash.pdf")
        blob.upload_from_file.assert_called_once()
        arguments = blob.upload_from_file.call_args.kwargs
        self.assertEqual(arguments["if_generation_match"], 0)
        self.assertEqual(arguments["checksum"], "crc32c")

    def test_concurrent_identical_cloud_save_converges_without_overwrite(self):
        storage, bucket = self.storage_with_bucket()
        blob = bucket.blob.return_value
        blob.upload_from_file.side_effect = PreconditionFailed("already exists")
        bucket.get_blob.return_value = blob
        with patch.object(ConflictSafeGoogleCloudStorage, "bucket", new_callable=PropertyMock, return_value=bucket):
            name = storage._save("scores/owner/hash.pdf", ContentFile(b"same", name="same.pdf"))
        self.assertEqual(name, "scores/owner/hash.pdf")
        bucket.get_blob.assert_called_once_with("scores/owner/hash.pdf")

    def test_cloud_deletes_are_guarded_by_the_observed_generation(self):
        storage, bucket = self.storage_with_bucket()
        source = MagicMock(generation=19)
        derived = [MagicMock(generation=31), MagicMock(generation=32)]
        bucket.get_blob.return_value = source
        bucket.list_blobs.return_value = derived
        with patch.object(ConflictSafeGoogleCloudStorage, "bucket", new_callable=PropertyMock, return_value=bucket):
            storage.delete("scores/owner/hash.pdf")
            storage.delete_prefix("derived/owner/hash/")
        self.assertEqual(source.delete.call_args.kwargs["if_generation_match"], 19)
        self.assertEqual([item.delete.call_args.kwargs["if_generation_match"] for item in derived], [31, 32])
