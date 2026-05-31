"""Storage abstraction for TIL attachments.

Dev: local disk under backend/data/uploads/ (zero config, no extra services).
Prod: Cloudflare R2 bucket (objects served via R2's public URL or a custom domain).

Selection is automatic based on which R2_* env vars are set. The rest of the
codebase doesn't care which backend is active — uploads, deletes, and
URL-construction all go through `get_storage()`.
"""

from __future__ import annotations

import io
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO

from app.config import UPLOADS_DIR, get_settings


class StorageBackend(ABC):
    """Common interface — three operations cover all our needs."""

    is_remote: bool = False

    @abstractmethod
    def save(self, key: str, body: BinaryIO, content_type: str) -> None: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def public_url(self, key: str) -> str:
        """Absolute URL that browsers can fetch. Empty string if unsupported."""


class LocalDiskStorage(StorageBackend):
    is_remote = False

    def save(self, key: str, body: BinaryIO, content_type: str) -> None:
        path = UPLOADS_DIR / key
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as out:
            while chunk := body.read(64 * 1024):
                out.write(chunk)

    def delete(self, key: str) -> None:
        (UPLOADS_DIR / key).unlink(missing_ok=True)

    def public_url(self, key: str) -> str:
        # Served by the FastAPI app at /uploads/<key>; consumers prepend API_BASE.
        return f"/uploads/{key}"


class R2Storage(StorageBackend):
    """Cloudflare R2 via the S3-compatible API. Public-read bucket assumed.

    We don't sign URLs because (a) all TIL attachments are public content
    anyway and (b) signed URLs need a backend round-trip per file. If a
    future feature needs private files we'll switch to presigned URLs.
    """

    is_remote = True

    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket: str,
        public_url: str,
    ) -> None:
        import boto3  # imported lazily so dev never has to pip-install boto3

        self.bucket = bucket
        self.public_base = public_url.rstrip("/")
        self.client = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )

    def save(self, key: str, body: BinaryIO, content_type: str) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType=content_type or "application/octet-stream",
            CacheControl="public, max-age=31536000, immutable",
        )

    def delete(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except Exception:  # noqa: BLE001 — defensive; deletes shouldn't break the API
            pass

    def public_url(self, key: str) -> str:
        if not self.public_base:
            return ""
        return f"{self.public_base}/{key}"


@lru_cache(maxsize=1)
def get_storage() -> StorageBackend:
    s = get_settings()
    if (
        s.r2_bucket
        and s.r2_account_id
        and s.r2_access_key_id
        and s.r2_secret_access_key
    ):
        return R2Storage(
            account_id=s.r2_account_id,
            access_key_id=s.r2_access_key_id,
            secret_access_key=s.r2_secret_access_key,
            bucket=s.r2_bucket,
            public_url=s.r2_public_url,
        )
    return LocalDiskStorage()


def reset_cache() -> None:
    """For tests that flip env vars between cases."""
    get_storage.cache_clear()
