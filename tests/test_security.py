"""
Tests for security utilities, sanitization, path traversal prevention, and API error safety.
"""
import io
import pytest
from app.utils import security
from app.services import file_service


def test_validate_password():
    assert security.validate_password("")[0] is False
    assert security.validate_password(None)[0] is False
    assert security.validate_password("A" * 300)[0] is False
    assert security.validate_password("ValidPassword123!")[0] is True


def test_validate_algorithm():
    assert security.validate_algorithm("")[0] is False
    assert security.validate_algorithm("DES")[0] is False
    assert security.validate_algorithm("AES-256-CBC")[0] is False
    assert security.validate_algorithm("AES-256-GCM")[0] is True
    assert security.validate_algorithm("ChaCha20-Poly1305")[0] is True


def test_validate_plaintext():
    assert security.validate_plaintext("")[0] is False
    assert security.validate_plaintext("Halo Dunia")[0] is True


def test_secure_filename_path_traversal():
    malicious_names = [
        "../../../../etc/passwd",
        "..\\..\\..\\Windows\\System32\\cmd.exe",
        "/etc/shadow",
        "nested/folder/file.txt",
    ]
    for bad_name in malicious_names:
        safe = file_service.get_safe_filename(bad_name)
        assert "/" not in safe
        assert "\\" not in safe
        assert ".." not in safe


def test_api_text_decrypt_error_does_not_leak_stack_trace(client):
    # Send deliberately invalid ciphertext
    res = client.post(
        "/api/decrypt/text",
        json={"ciphertext_b64": "invalid_base64_payload", "password": "wrongpassword"},
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    # Error message must be user-friendly without Python tracebacks
    assert "Traceback" not in data["message"]
    assert "password salah atau data telah dimodifikasi" in data["message"]


def test_api_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
