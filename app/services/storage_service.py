"""Private Supabase Storage adapter for encrypted Brankas files."""
import re
from typing import Any, Callable

from config import Config


class StorageError(Exception):
    """Base error for storage operations."""


class StorageNotConfigured(StorageError):
    """Supabase credentials are not configured."""


class StorageNotFound(StorageError):
    """Requested encrypted object does not exist."""


_FILE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_OWNER_ID_RE = _FILE_ID_RE


class StorageService:
    """Small, lazy Supabase Storage wrapper.

    The Supabase client is created only when a storage operation is requested,
    keeping local development and tests independent from Supabase credentials.
    """

    def __init__(
        self,
        config: type = Config,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.config = config
        self._client_factory = client_factory
        self._client: Any | None = None

    def is_configured(self) -> bool:
        return bool(
            self.config.SUPABASE_URL
            and self.config.SUPABASE_SERVICE_ROLE_KEY
            and self.config.SUPABASE_STORAGE_BUCKET
        )

    def _get_bucket(self) -> Any:
        if not self.is_configured():
            raise StorageNotConfigured(
                "Supabase Storage belum dikonfigurasi di environment server."
            )

        api_key = self.config.SUPABASE_SERVICE_ROLE_KEY
        bucket_name = self.config.SUPABASE_STORAGE_BUCKET
        if api_key.startswith("sb_publishable_"):
            raise StorageError(
                "SUPABASE_SERVICE_ROLE_KEY harus menggunakan secret key server-side."
            )
        if bucket_name.startswith(("sb_secret_", "sb_publishable_")):
            raise StorageError(
                "SUPABASE_STORAGE_BUCKET harus berisi nama bucket, bukan API key."
            )

        if self._client is None:
            try:
                if self._client_factory is None:
                    from supabase import create_client
                    self._client_factory = create_client
                self._client = self._client_factory(
                    self.config.SUPABASE_URL,
                    api_key,
                )
                if api_key.startswith("sb_secret_"):
                    headers = getattr(getattr(self._client, "options", None), "headers", None)
                    if isinstance(headers, dict):
                        headers.pop("Authorization", None)
            except Exception as exc:
                raise StorageError("Supabase Storage tidak dapat diinisialisasi.") from exc

        try:
            return self._client.storage.from_(self.config.SUPABASE_STORAGE_BUCKET)
        except Exception as exc:
            raise StorageError("Bucket Supabase Storage tidak dapat diakses.") from exc

    @staticmethod
    def build_path(owner_id: str, file_id: str) -> str:
        if not _OWNER_ID_RE.fullmatch(owner_id or ""):
            raise StorageError("Owner storage tidak valid.")
        if not _FILE_ID_RE.fullmatch(file_id or ""):
            raise StorageError("ID file storage tidak valid.")
        return f"users/{owner_id}/{file_id}.enc"

    def upload(self, path: str, data: bytes, content_type: str) -> None:
        try:
            self._get_bucket().upload(
                path,
                data,
                file_options={
                    "content-type": content_type,
                    "upsert": False,
                },
            )
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError("File terenkripsi gagal disimpan ke Supabase Storage.") from exc

    def download(self, path: str) -> bytes:
        try:
            data = self._get_bucket().download(path)
            if not data:
                raise StorageNotFound("File storage kosong atau tidak ditemukan.")
            return bytes(data)
        except StorageError:
            raise
        except Exception as exc:
            raise StorageNotFound("File terenkripsi tidak ditemukan di storage.") from exc

    def remove(self, path: str) -> None:
        try:
            self._get_bucket().remove([path])
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError("File terenkripsi gagal dihapus dari storage.") from exc

    def list(self, prefix: str) -> list[dict[str, Any]]:
        if not _OWNER_ID_RE.fullmatch(prefix or ""):
            raise StorageError("Prefix storage tidak valid.")
        try:
            result = self._get_bucket().list(f"users/{prefix}")
            return result if isinstance(result, list) else []
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError("Daftar file storage tidak dapat dimuat.") from exc
