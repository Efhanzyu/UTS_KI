"""
Tests for text and file encryption/decryption service.
"""
import pytest
from cryptography.exceptions import InvalidTag
from app.services import encryption_service
from app.crypto.container import ContainerError


@pytest.mark.parametrize("algorithm", ["AES-256-GCM", "ChaCha20-Poly1305"])
def test_text_encryption_roundtrip(algorithm, sample_plaintext, sample_password):
    enc_result = encryption_service.encrypt_text(sample_plaintext, sample_password, algorithm)
    assert "ciphertext_b64" in enc_result
    assert enc_result["algorithm"] == algorithm

    decrypted = encryption_service.decrypt_text(enc_result["ciphertext_b64"], sample_password)
    assert decrypted == sample_plaintext


@pytest.mark.parametrize("algorithm", ["AES-256-GCM", "ChaCha20-Poly1305"])
def test_text_decrypt_wrong_password(algorithm, sample_plaintext, sample_password):
    enc_result = encryption_service.encrypt_text(sample_plaintext, sample_password, algorithm)
    
    with pytest.raises(InvalidTag):
        encryption_service.decrypt_text(enc_result["ciphertext_b64"], "WrongPassword123!")


@pytest.mark.parametrize("algorithm", ["AES-256-GCM", "ChaCha20-Poly1305"])
def test_file_encryption_roundtrip(algorithm, sample_file_bytes, sample_password):
    orig_name = "tugas_keamanan.pdf"
    orig_mime = "application/pdf"

    enc_bytes = encryption_service.encrypt_file(
        file_bytes=sample_file_bytes,
        password=sample_password,
        algorithm=algorithm,
        original_filename=orig_name,
        mime_type=orig_mime,
    )
    assert isinstance(enc_bytes, bytes)
    assert len(enc_bytes) > len(sample_file_bytes)

    dec_result = encryption_service.decrypt_file(enc_bytes, sample_password)
    assert dec_result["file_bytes"] == sample_file_bytes
    assert dec_result["original_filename"] == orig_name
    assert dec_result["mime_type"] == orig_mime
    assert dec_result["algorithm"] == algorithm


def test_file_decrypt_wrong_password(sample_file_bytes, sample_password):
    enc_bytes = encryption_service.encrypt_file(
        file_bytes=sample_file_bytes,
        password=sample_password,
        algorithm="AES-256-GCM",
        original_filename="doc.pdf",
    )
    with pytest.raises(InvalidTag):
        encryption_service.decrypt_file(enc_bytes, "SandiSalahTotal!")


def test_file_decrypt_tampered_file(sample_file_bytes, sample_password):
    enc_bytes = bytearray(
        encryption_service.encrypt_file(
            file_bytes=sample_file_bytes,
            password=sample_password,
            algorithm="AES-256-GCM",
            original_filename="doc.pdf",
        )
    )
    # Modify byte in ciphertext area (at the end)
    enc_bytes[-1] ^= 0x01

    with pytest.raises(InvalidTag):
        encryption_service.decrypt_file(bytes(enc_bytes), sample_password)
