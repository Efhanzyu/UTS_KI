import io

import pytest

from app.routes import api as api_routes
from app.services.storage_service import (
    StorageError,
    StorageNotConfigured,
    StorageService,
)
from config import Config


class StorageTestConfig:
    SUPABASE_URL = "https://example.supabase.co"
    SUPABASE_SERVICE_ROLE_KEY = "test-service-role-key"
    SUPABASE_STORAGE_BUCKET = "brankas-files"


class FakeBucket:
    def __init__(self):
        self.files = {}

    def upload(self, path, data, file_options=None):
        if path in self.files:
            raise RuntimeError("already exists")
        self.files[path] = bytes(data)

    def download(self, path):
        if path not in self.files:
            raise RuntimeError("not found")
        return self.files[path]

    def remove(self, paths):
        for path in paths:
            self.files.pop(path, None)

    def list(self, prefix):
        return [{"name": path.rsplit("/", 1)[-1]} for path in self.files if path.startswith(prefix + "/")]


class FakeStorage:
    def __init__(self, bucket):
        self.bucket = bucket

    def from_(self, bucket_name):
        assert bucket_name == "brankas-files"
        return self.bucket


class FakeClient:
    def __init__(self, bucket):
        self.storage = FakeStorage(bucket)


def test_storage_service_upload_download_list_delete():
    bucket = FakeBucket()
    service = StorageService(StorageTestConfig, lambda url, key: FakeClient(bucket))
    path = service.build_path("a" * 32, "b" * 32)

    service.upload(path, b"encrypted-bytes", "application/octet-stream")
    assert service.download(path) == b"encrypted-bytes"
    assert service.list("a" * 32)[0]["name"] == ("b" * 32) + ".enc"

    service.remove(path)
    with pytest.raises(StorageError):
        service.download(path)


def test_storage_service_requires_configuration():
    class MissingConfig:
        SUPABASE_URL = ""
        SUPABASE_SERVICE_ROLE_KEY = ""
        SUPABASE_STORAGE_BUCKET = "brankas-files"

    service = StorageService(MissingConfig)
    assert service.is_configured() is False
    with pytest.raises(StorageNotConfigured):
        service.download("users/path")


def test_storage_service_rejects_publishable_key_for_backend():
    class PublishableKeyConfig(StorageTestConfig):
        SUPABASE_SERVICE_ROLE_KEY = "sb_publishable_test-key"

    service = StorageService(PublishableKeyConfig, lambda url, key: pytest.fail("client must not be created"))
    with pytest.raises(StorageError, match="secret key"):
        service._get_bucket()


def test_storage_service_rejects_api_key_as_bucket_name():
    class InvalidBucketConfig(StorageTestConfig):
        SUPABASE_STORAGE_BUCKET = "sb_secret_test-key"

    service = StorageService(InvalidBucketConfig, lambda url, key: pytest.fail("client must not be created"))
    with pytest.raises(StorageError, match="nama bucket"):
        service._get_bucket()


def test_secret_key_is_sent_as_api_key_not_bearer():
    class SecretKeyConfig(StorageTestConfig):
        SUPABASE_SERVICE_ROLE_KEY = "sb_secret_test-key"

    service = StorageService(SecretKeyConfig)
    service._get_bucket()

    headers = service._client.options.headers
    assert headers["apiKey"] == "sb_secret_test-key"
    assert "Authorization" not in headers


def test_storage_service_rejects_arbitrary_paths():
    with pytest.raises(StorageError):
        StorageService.build_path("../escape", "file")
    with pytest.raises(StorageError):
        StorageService.build_path("a" * 32, "../escape")


def test_file_route_persists_and_manages_encrypted_object(client, monkeypatch):
    bucket = FakeBucket()
    service = StorageService(StorageTestConfig, lambda url, key: FakeClient(bucket))
    monkeypatch.setattr(api_routes, "_storage", service)
    monkeypatch.setattr(Config, "PBKDF2_ITERATIONS", 1000)

    encrypted = client.post(
        "/api/encrypt/file",
        data={
            "file": (io.BytesIO(b"private document"), "notes.txt"),
            "password": "strong-password",
            "algorithm": "AES-256-GCM",
        },
        content_type="multipart/form-data",
    )
    assert encrypted.status_code == 200
    assert encrypted.headers["X-Brankas-Storage-Id"]

    stored = client.get("/api/storage/files")
    assert stored.status_code == 200
    file_entry = stored.get_json()["data"]["files"][0]
    assert file_entry["original_filename"] == "notes.txt"

    downloaded = client.get(f"/api/storage/files/{file_entry['id']}")
    assert downloaded.status_code == 200
    decrypted = client.post(
        f"/api/storage/files/{file_entry['id']}/decrypt",
        json={"password": "strong-password"},
    )
    assert decrypted.status_code == 200
    assert decrypted.data == b"private document"

    deleted = client.delete(f"/api/storage/files/{file_entry['id']}")
    assert deleted.status_code == 200
    assert client.get("/api/storage/files").get_json()["data"]["files"] == []
