"""Roundtrip all ten supplied file samples and compare their byte hashes."""
import hashlib
from pathlib import Path

import pytest
from config import Config
from app.services import encryption_service


SAMPLES = sorted(Path("test_files").glob("*"))


@pytest.mark.parametrize("sample_path", SAMPLES, ids=lambda path: path.name)
def test_supplied_sample_file_roundtrips_byte_for_byte(sample_path, monkeypatch):
    monkeypatch.setattr(Config, "PBKDF2_ITERATIONS", 1000)
    original = sample_path.read_bytes()
    encrypted = encryption_service.encrypt_file(
        file_bytes=original,
        password="test-only-password",
        algorithm="AES-256-GCM",
        original_filename=sample_path.name,
    )
    restored = encryption_service.decrypt_file(encrypted, "test-only-password")["file_bytes"]
    assert hashlib.sha256(restored).digest() == hashlib.sha256(original).digest()
    assert restored == original


def test_exactly_ten_supplied_file_samples_are_available():
    assert len(SAMPLES) == 10
