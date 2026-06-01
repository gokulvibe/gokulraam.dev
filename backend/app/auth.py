from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Response, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from passlib.context import CryptContext

from app.config import Settings, get_settings


pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
SESSION_COOKIE = "gokulraam_session"
FRIEND_COOKIE = "gokulraam_friend_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days
FRIEND_SESSION_MAX_AGE = 60 * 60 * 24 * 180  # 180 days — friends shouldn't have to re-enter often


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


def _friend_serializer(secret: str) -> URLSafeTimedSerializer:
    # Separate salt so an admin token can't be confused for a friend token
    # or vice versa.
    return URLSafeTimedSerializer(secret, salt="gokulraam-friend-v1")


def issue_session(response: Response, username: str, settings: Settings) -> None:
    token = _serializer(settings.session_secret).dumps({"u": username})
    # Cross-origin in prod (frontend on Pages, backend on Render) → cookie
    # must be SameSite=None + Secure, otherwise the browser silently refuses
    # to store it. Locally (cookie_secure=false) we use Lax/insecure so dev
    # over http://localhost keeps working.
    samesite_value: str = "none" if settings.cookie_secure else "lax"
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite=samesite_value,  # type: ignore[arg-type]
        secure=settings.cookie_secure,
    )


def clear_session(response: Response) -> None:
    # Must match the attributes used when setting the cookie or the browser
    # won't delete it (some browsers compare SameSite/Secure on deletion).
    settings = get_settings()
    samesite_value: str = "none" if settings.cookie_secure else "lax"
    response.delete_cookie(
        SESSION_COOKIE,
        samesite=samesite_value,  # type: ignore[arg-type]
        secure=settings.cookie_secure,
    )


def issue_friend_session(response: Response, settings: Settings) -> None:
    """Marks the browser as a 'friend' — granted access to /museum.
    Stored separately from the admin cookie so revoking one doesn't
    accidentally drop the other."""
    token = _friend_serializer(settings.session_secret).dumps({"f": True})
    samesite_value: str = "none" if settings.cookie_secure else "lax"
    response.set_cookie(
        FRIEND_COOKIE,
        token,
        max_age=FRIEND_SESSION_MAX_AGE,
        httponly=True,
        samesite=samesite_value,  # type: ignore[arg-type]
        secure=settings.cookie_secure,
    )


def clear_friend_session(response: Response) -> None:
    settings = get_settings()
    samesite_value: str = "none" if settings.cookie_secure else "lax"
    response.delete_cookie(
        FRIEND_COOKIE,
        samesite=samesite_value,  # type: ignore[arg-type]
        secure=settings.cookie_secure,
    )


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


def _decode_friend(token: str | None, settings: Settings) -> bool:
    if not token:
        return False
    try:
        _friend_serializer(settings.session_secret).loads(
            token, max_age=FRIEND_SESSION_MAX_AGE
        )
        return True
    except (SignatureExpired, BadSignature):
        return False


def museum_visitor(
    settings: Annotated[Settings, Depends(get_settings)],
    admin_session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
    friend_session: Annotated[str | None, Cookie(alias=FRIEND_COOKIE)] = None,
) -> str:
    """Allows /museum access for either admin or friend cookie. Raises 401
    otherwise. Returns 'admin' or 'friend' so the caller can branch on role
    if needed."""
    if _decode_session(admin_session, settings):
        return "admin"
    if _decode_friend(friend_session, settings):
        return "friend"
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "museum access required")


def optional_museum_visitor(
    settings: Annotated[Settings, Depends(get_settings)],
    admin_session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
    friend_session: Annotated[str | None, Cookie(alias=FRIEND_COOKIE)] = None,
) -> str | None:
    """Non-raising variant for endpoints/pages that want to distinguish
    visitors without rejecting them."""
    if _decode_session(admin_session, settings):
        return "admin"
    if _decode_friend(friend_session, settings):
        return "friend"
    return None
