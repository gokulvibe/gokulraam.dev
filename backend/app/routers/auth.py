from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from app.auth import (
    clear_friend_session,
    clear_session,
    current_admin,
    issue_friend_session,
    issue_session,
    verify_password,
)
from app.config import Settings, get_settings
from app.schemas import LoginIn


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    body: LoginIn,
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    if body.username != settings.admin_username or not verify_password(
        body.password, settings.admin_password_hash
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    issue_session(response, body.username, settings)
    return {"status": "ok"}


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    clear_session(response)
    return {"status": "ok"}


@router.get("/me")
def me(user: Annotated[str, Depends(current_admin)]) -> dict[str, str]:
    return {"username": user}


# ─── Friend access (museum) ─────────────────────────────────────


class FriendCodeIn(BaseModel):
    code: str


@router.post("/museum-enter")
def museum_enter(
    body: FriendCodeIn,
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    if not settings.friend_code:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "museum is not configured",
        )
    if body.code != settings.friend_code:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "wrong code")
    issue_friend_session(response, settings)
    return {"status": "ok"}


@router.post("/museum-leave")
def museum_leave(response: Response) -> dict[str, str]:
    clear_friend_session(response)
    return {"status": "ok"}
