"""
Tests for container format (.enc) pack and unpack.
"""
import pytest
from app.crypto import container


@pytest.fixture
def sample_pack_args():
    return {
        "algorithm": "AES-256-GCM",
        "kdf": "PBKDF2-HMAC-SHA256",
        "pbkdf2_iterations": 600000,
        "salt": b"S" * 32,
        "nonce": b"N" * 12,
        "ciphertext": b"encrypted_payload_data_with_tag16b",
        "original_filename": "tugas_keamanan.pdf",
        "mime_type": "application/pdf",
    }


def test_pack_and_unpack_roundtrip(sample_pack_args):
    packed = container.pack_encrypted_file(**sample_pack_args)
    assert packed.startswith(container.MAGIC)
    
    unpacked = container.unpack_encrypted_file(packed)
    assert unpacked["algorithm"] == sample_pack_args["algorithm"]
    assert unpacked["kdf"] == sample_pack_args["kdf"]
    assert unpacked["pbkdf2_iterations"] == sample_pack_args["pbkdf2_iterations"]
    assert unpacked["salt"] == sample_pack_args["salt"]
    assert unpacked["nonce"] == sample_pack_args["nonce"]
    assert unpacked["ciphertext"] == sample_pack_args["ciphertext"]
    assert unpacked["original_filename"] == sample_pack_args["original_filename"]
    assert unpacked["mime_type"] == sample_pack_args["mime_type"]


def test_unpack_magic_error(sample_pack_args):
    packed = bytearray(container.pack_encrypted_file(**sample_pack_args))
    packed[:8] = b"CORRUPTD"
    
    with pytest.raises(container.MagicError):
        container.unpack_encrypted_file(bytes(packed))


def test_unpack_version_error(sample_pack_args):
    packed = bytearray(container.pack_encrypted_file(**sample_pack_args))
    # Version is at offset 8..10
    packed[8:10] = b"\x99\x99"
    
    with pytest.raises(container.VersionError):
        container.unpack_encrypted_file(bytes(packed))


def test_unpack_too_small():
    with pytest.raises(container.MetadataError):
        container.unpack_encrypted_file(b"SHORT")


def test_unpack_corrupted_header(sample_pack_args):
    packed = bytearray(container.pack_encrypted_file(**sample_pack_args))
    # Corrupt the header area
    packed[15] = 0xFF
    packed[16] = 0xFF
    with pytest.raises(container.MetadataError):
        container.unpack_encrypted_file(bytes(packed))


def test_unpack_unsupported_algorithm(sample_pack_args):
    packed = container.pack_encrypted_file(**sample_pack_args)
    tampered = packed.replace(b"AES-256-GCM", b"DES-DES-GCM")
    with pytest.raises(container.AlgorithmError):
        container.unpack_encrypted_file(tampered)
