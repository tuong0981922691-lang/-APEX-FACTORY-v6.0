"""Auth router — existing endpoints (register/login/me/logout)."""
import secrets

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from apex_core.auth.session_store import SessionStore
from apex_core.auth.user_store import UserStore

router = APIRouter(prefix="/api/auth", tags=["auth"])

user_store = UserStore()
session_store = SessionStore()


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


@router.get("/health")
def auth_health():
    return {"ok": True, "module": "auth"}


@router.post("/register")
def register(req: RegisterRequest):
    if user_store.get_by_email(req.email):
        raise HTTPException(400, "Email already registered")
    user = user_store.create(email=req.email, password=req.password, name=req.name)
    return {"user_id": user["id"], "email": user["email"]}


@router.post("/login")
def login(req: LoginRequest, response: Response):
    user = user_store.verify(req.email, req.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    token = secrets.token_urlsafe(32)
    session_store.create(token=token, user_id=user["id"])
    response.set_cookie("session_token", token, httponly=True, samesite="lax")
    return {"ok": True, "user_id": user["id"]}


@router.get("/me")
def me(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(401, "Not authenticated")
    session = session_store.get(token)
    if not session:
        raise HTTPException(401, "Session expired")
    user = user_store.get_by_id(session["user_id"])
    if not user:
        raise HTTPException(401, "User not found")
    return {"user_id": user["id"], "email": user["email"], "name": user.get("name", "")}


@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        session_store.delete(token)
    response.delete_cookie("session_token")
    return {"ok": True}
