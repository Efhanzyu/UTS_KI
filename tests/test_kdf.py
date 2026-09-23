"""
Tests for Key Derivation Function (PBKDF2-HMAC-SHA256).
"""
import pytest
from app.crypto import kdf


def test_generate_salt_length():
    salt = kdf.generate_salt()
    assert isinstance(salt, bytes)
    assert len(salt) == kdf.SALT_SIZE
    assert len(salt) == 32


def test_generate_salt_randomness():
    salt1 = kdf.generate_salt()
    salt2 = kdf.generate_salt()
    assert salt1 != salt2


def test_derive_key_length(sample_password):
    salt = kdf.generate_salt()
    key = kdf.derive_key(sample_password, salt, iterations=1000)
    assert isinstance(key, bytes)
    assert len(key) == kdf.KEY_SIZE
    assert len(key) == 32


def test_derive_key_determinism(sample_password):
    salt = kdf.generate_salt()
    key1 = kdf.derive_key(sample_password, salt, iterations=1000)
    key2 = kdf.derive_key(sample_password, salt, iterations=1000)
    assert key1 == key2


def test_derive_key_different_passwords():
    salt = kdf.generate_salt()
    key1 = kdf.derive_key("PasswordA_123", salt, iterations=1000)
    key2 = kdf.derive_key("PasswordB_123", salt, iterations=1000)
    assert key1 != key2


def test_derive_key_different_salts(sample_password):
    salt1 = kdf.generate_salt()
    salt2 = kdf.generate_salt()
    key1 = kdf.derive_key(sample_password, salt1, iterations=1000)
    key2 = kdf.derive_key(sample_password, salt2, iterations=1000)
    assert key1 != key2


def test_derive_key_different_iterations(sample_password):
    salt = kdf.generate_salt()
    key1 = kdf.derive_key(sample_password, salt, iterations=1000)
    key2 = kdf.derive_key(sample_password, salt, iterations=2000)
    assert key1 != key2
