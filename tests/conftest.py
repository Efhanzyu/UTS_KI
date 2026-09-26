"""
Pytest configuration and test fixtures for Brankas File Tugas Kuliah.
"""
import pytest
from app import create_app
from config import Config


class TestConfig(Config):
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    # Use smaller KDF iterations in unit tests for high-speed test suites
    PBKDF2_ITERATIONS = 10000
    BENCHMARK_KDF_ITERATIONS = 1000
    BENCHMARK_RUNS = 2


@pytest.fixture
def app():
    """Create and configure a testing Flask app instance."""
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
