from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    admin_username: str = "gokul"
    admin_password_hash: str = ""
    session_secret: str = "dev-secret-change-me"
    # Comma-separated list of allowed frontend origins (e.g. for prod + previews)
    frontend_origin: str = "http://localhost:4321"

    # Cookie security: set `cookie_secure=true` in production. Doing so flips
    # the session cookie to SameSite=None + Secure (required when the frontend
    # and backend are on different origins). Locally we use Lax/insecure so
    # cookies still work over plain http://localhost.
    cookie_secure: bool = False

    # Defaults to SQLite at backend/data/app.db. Production overrides with
    # a postgres:// URL (Render env var). SQLAlchemy handles the dialect.
    database_url: str = f"sqlite:///{DATA_DIR / 'app.db'}"

    # ─── Cloudflare R2 (optional; falls back to local disk if unset) ──
    # In production, set ALL of these via the Render dashboard.
    # Public URL is the file-serving CDN URL: either the auto-generated
    # `https://pub-XXXX.r2.dev` or a custom domain you map to the bucket.
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = ""
    r2_public_url: str = ""


@lru_cache
def get_settings() -> Settings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()
