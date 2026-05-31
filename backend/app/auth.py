from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Response, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from passlib.context import CryptContext

from app.config import Settings, get_settings


pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
SESSION_COOKIE = "gokulraam_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def hash_password(plain: str) -> str:
    return pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return pwd.verify(plain, hashed)
    except ValueError:
        return False


def _serializer(secret: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret, salt="gokulraam-session-v1")


def issue_session(response: Response, username: str, settings: Settings) -> None:
    token = _serializer(settings.session_secret).dumps({"u": username})
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,  # set True behind HTTPS in prod
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE)


def _decode_session(session: str | None, settings: Settings) -> str | None:
    """Returns the admin username if the cookie is valid, else None. Never raises."""
    if not session:
        return None
    try:
        data = _serializer(settings.session_secret).loads(session, max_age=SESSION_MAX_AGE)
    except (SignatureExpired, BadSignature):
        return None
    username = data.get("u")
    return username if username == settings.admin_username else None


def current_admin(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> str:
    username = _decode_session(session, settings)
    if not username:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")
    return username


def optional_admin(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> str | None:
    """Same as `current_admin` but returns None instead of raising for guests.

    Use on endpoints that show different data to admin vs guest.
    """
    return _decode_session(session, settings)
