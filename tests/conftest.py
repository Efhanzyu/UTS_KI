"""
Pytest configuration and test fixtures for Brankas File Tugas Kuliah.
"""
import pytest
from app import create_app
from app.routes import api as api_routes
from app.services.storage_service import StorageService
from config import Config


class TestConfig(Config):
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    # Use smaller KDF iterations in unit tests for high-speed test suites
    PBKDF2_ITERATIONS = 10000
    BENCHMARK_KDF_ITERATIONS = 1000
    BENCHMARK_RUNS = 2
    SUPABASE_URL = ""
    SUPABASE_SERVICE_ROLE_KEY = ""
    SUPABASE_STORAGE_BUCKET = "brankas-files"


@pytest.fixture
def app(monkeypatch):
    """Create and configure a testing Flask app instance."""
    monkeypatch.setattr(api_routes, "_storage", StorageService(TestConfig))
    app_instance = create_app(TestConfig)
    return app_instance


@pytest.fixture
def client(app):
    """Test client for HTTP requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_password():
    return "SandiRahasiaMahasiswa2026!"


@pytest.fixture
def sample_plaintext():
    return "Laporan Tugas Akhir Keamanan Informasi Mahasiswa Teknik Informatika."


@pytest.fixture
def sample_file_bytes():
    return b"%PDF-1.4\n1 0 obj\n<< /Title (Laporan Tugas Kuliah) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
