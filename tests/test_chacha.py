"""
Tests for ChaCha20-Poly1305 encryption and decryption.
"""
import os
import pytest
from cryptography.exceptions import InvalidTag
from app.crypto import chacha20


@pytest.fixture
def chacha_key():
    return os.urandom(32)


def test_chacha_generate_nonce():
    nonce = chacha20.generate_nonce()
    assert isinstance(nonce, bytes)
    assert len(nonce) == chacha20.NONCE_SIZE
    assert len(nonce) == 12


def test_chacha_encrypt_decrypt_roundtrip(chacha_key, sample_plaintext):
    nonce = chacha20.generate_nonce()
    plaintext_bytes = sample_plaintext.encode("utf-8")
    
    ciphertext = chacha20.encrypt(chacha_key, plaintext_bytes, nonce)
    assert len(ciphertext) == len(plaintext_bytes) + 16  # 16-byte Poly1305 tag
    
    decrypted = chacha20.decrypt(chacha_key, ciphertext, nonce)
    assert decrypted == plaintext_bytes
    assert decrypted.decode("utf-8") == sample_plaintext


def test_chacha_decrypt_wrong_key(chacha_key, sample_plaintext):
    nonce = chacha20.generate_nonce()
    ciphertext = chacha20.encrypt(chacha_key, sample_plaintext.encode("utf-8"), nonce)
    wrong_key = os.urandom(32)
    
    with pytest.raises(InvalidTag):
        chacha20.decrypt(wrong_key, ciphertext, nonce)


def test_chacha_decrypt_wrong_nonce(chacha_key, sample_plaintext):
    nonce = chacha20.generate_nonce()
    ciphertext = chacha20.encrypt(chacha_key, sample_plaintext.encode("utf-8"), nonce)
    wrong_nonce = chacha20.generate_nonce()
    
    with pytest.raises(InvalidTag):
        chacha20.decrypt(chacha_key, ciphertext, wrong_nonce)


def test_chacha_decrypt_tampered_ciphertext(chacha_key, sample_plaintext):
    nonce = chacha20.generate_nonce()
    ciphertext = bytearray(chacha20.encrypt(chacha_key, sample_plaintext.encode("utf-8"), nonce))
    ciphertext[0] ^= 0x01
    
    with pytest.raises(InvalidTag):
        chacha20.decrypt(chacha_key, bytes(ciphertext), nonce)
