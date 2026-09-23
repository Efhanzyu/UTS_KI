"""Application configuration and secret handling."""
import os
import secrets
from dotenv import load_dotenv
load_dotenv()

def resolve_secret_key(secret_key: str | None, environment: str) -> str:
    if secret_key:
        return secret_key
    if environment.lower() == "production":
        raise RuntimeError("SECRET_KEY must be set in production.")
    return secrets.token_hex(32)

_ENVIRONMENT=os.environ.get("FLASK_ENV","development").lower()
_SECRET_KEY=resolve_secret_key(os.environ.get("SECRET_KEY"),_ENVIRONMENT)

class Config:
    SECRET_KEY: str = _SECRET_KEY
    DEBUG: bool = _ENVIRONMENT == "development"
    PBKDF2_ITERATIONS: int = int(os.environ.get("PBKDF2_ITERATIONS",600_000))
    MAX_CONTENT_MB: int = int(os.environ.get("MAX_CONTENT_MB",64))
    MAX_CONTENT_LENGTH: int = MAX_CONTENT_MB*1024*1024
    BENCHMARK_KDF_ITERATIONS: int = int(os.environ.get("BENCHMARK_KDF_ITERATIONS",1_000))
    BENCHMARK_RUNS: int = int(os.environ.get("BENCHMARK_RUNS",10))
    BENCHMARK_MAX_RUNS: int = 100
