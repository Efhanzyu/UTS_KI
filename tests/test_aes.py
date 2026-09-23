"""
Tests for AES-256-GCM encryption and decryption.
"""
import os
import pytest
from cryptography.exceptions import InvalidTag
from app.crypto import aes_gcm


@pytest.fixture
def aes_key():
    return os.urandom(32)


def test_aes_generate_nonce():
    nonce = aes_gcm.generate_nonce()
    assert isinstance(nonce, bytes)
    assert len(nonce) == aes_gcm.NONCE_SIZE
    assert len(nonce) == 12


def test_aes_encrypt_decrypt_roundtrip(aes_key, sample_plaintext):
    nonce = aes_gcm.generate_nonce()
    plaintext_bytes = sample_plaintext.encode("utf-8")
    
    ciphertext = aes_gcm.encrypt(aes_key, plaintext_bytes, nonce)
    assert len(ciphertext) == len(plaintext_bytes) + 16  # 16-byte auth tag
    
    decrypted = aes_gcm.decrypt(aes_key, ciphertext, nonce)
    assert decrypted == plaintext_bytes
    assert decrypted.decode("utf-8") == sample_plaintext


def test_aes_decrypt_wrong_key(aes_key, sample_plaintext):
    nonce = aes_gcm.generate_nonce()
    ciphertext = aes_gcm.encrypt(aes_key, sample_plaintext.encode("utf-8"), nonce)
    wrong_key = os.urandom(32)
    
    with pytest.raises(InvalidTag):
        aes_gcm.decrypt(wrong_key, ciphertext, nonce)


def test_aes_decrypt_wrong_nonce(aes_key, sample_plaintext):
    nonce = aes_gcm.generate_nonce()
    ciphertext = aes_gcm.encrypt(aes_key, sample_plaintext.encode("utf-8"), nonce)
    wrong_nonce = aes_gcm.generate_nonce()
    
    with pytest.raises(InvalidTag):
        aes_gcm.decrypt(aes_key, ciphertext, wrong_nonce)


def test_aes_decrypt_tampered_ciphertext(aes_key, sample_plaintext):
    nonce = aes_gcm.generate_nonce()
    ciphertext = bytearray(aes_gcm.encrypt(aes_key, sample_plaintext.encode("utf-8"), nonce))
    # Flip the first byte
    ciphertext[0] ^= 0x01
    
    with pytest.raises(InvalidTag):
        aes_gcm.decrypt(aes_key, bytes(ciphertext), nonce)
