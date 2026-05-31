from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth import clear_session, current_admin, issue_session, verify_password
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
