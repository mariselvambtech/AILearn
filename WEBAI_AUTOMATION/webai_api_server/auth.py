"""
Authentication and authorization utilities.

This file is the "bouncer" of the WebAI API server (see walkthrough.md →
"Component 1: The Warehouse"). It handles three security jobs:

1. **Password hashing** — scramble user passwords with bcrypt so they are
   never stored in plain text. We can check a login password against the
   hash, but we cannot reverse the hash back into the password.

2. **JWT tokens** — issue time-limited access tokens (JSON Web Tokens) that
   prove a user is logged in. These expire after `ACCESS_TOKEN_EXPIRE_MINUTES`
   (default 60 minutes).

3. **API keys** — generate long random keys that scripts use to authenticate
   without sending a username/password each time. The browser robot and the
   runner scripts send this key in the `X-API-Key` HTTP header.

Settings are read from the `.env` file (see `webai_api_server/.env`):
    SECRET_KEY                  — secret used to sign JWT tokens (keep it secret!)
    ALGORITHM                   — JWT signing algorithm (default HS256)
    ACCESS_TOKEN_EXPIRE_MINUTES — how long a login token stays valid
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
import secrets
import os
from dotenv import load_dotenv

from database import get_db
import models

load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check whether a plain-text login password matches the stored hash.

    This is a one-way check: bcrypt scrambles the plain password with the
    same salt used to make the hash, then compares the results. The original
    password can never be recovered from the hash.

    Args:
        plain_password (str): The password the user just typed at login.
        hashed_password (str): The scrambled password stored in the
            `users.password_hash` column (created by `get_password_hash`).

    Returns:
        bool: True if the password matches the hash, False otherwise.

    Example:
        >>> verify_password("secret123", "$2b$12$...")
        True
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Scramble a plain-text password into a bcrypt hash for safe storage.

    The hash includes a random salt, so the same password produces a
    different hash each time. Store the returned string in
    `users.password_hash`. Never store the plain password.

    Args:
        password (str): The plain-text password the user chose at registration.

    Returns:
        str: A bcrypt hash string like "$2b$12$N9qo8uLOickgx2Z...".

    Example:
        >>> get_password_hash("secret123")
        '$2b$12$N9qo8uLOickgx2ZMRZoE.M...'
    """
    return pwd_context.hash(password)


def generate_api_key() -> str:
    """
    Create a long random API key for a user.

    The key is what scripts (the browser robot, runner scripts) send in the
    `X-API-Key` HTTP header to prove who they are, instead of sending the
    user's password on every request. It is generated once at registration
    and stored in `users.api_key`.

    Returns:
        str: A 43-character URL-safe random string.

    Example:
        >>> generate_api_key()
        'o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8'
    """
    return secrets.token_urlsafe(32)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Build a signed JWT access token that proves a user is logged in.

    The token encodes the supplied `data` (usually `{"sub": username}`) plus
    an expiry time, then signs it with `SECRET_KEY` so it cannot be tampered
    with. The client sends it back as a `Bearer` token on protected routes.

    Args:
        data (dict): Payload to encode, e.g. `{"sub": "mariselvam"}`.
            "sub" (subject) is the standard JWT claim for the username.
        expires_delta (Optional[timedelta]): How long the token is valid.
            If None, defaults to `ACCESS_TOKEN_EXPIRE_MINUTES` (60 minutes).

    Returns:
        str: A signed JWT string (three dot-separated base64 segments).

    Example:
        >>> create_access_token({"sub": "alice"}, timedelta(minutes=30))
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str):
    """
    Look up a user by username and check their password.

    Used by the `POST /auth/login` endpoint. If the username does not exist
    or the password is wrong, returns False so the endpoint can raise a
    401 Unauthorized.

    Args:
        db (Session): An open SQLAlchemy database session.
        username (str): The username typed at login.
        password (str): The plain-text password typed at login.

    Returns:
        User | False: The `models.User` object on success, or False if the
        username is unknown or the password does not match.

    Example:
        >>> user = authenticate_user(db, "mariselvam", "secret123")
        >>> user.username
        'mariselvam'
    """
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


def get_current_user_by_token(token: str, db: Session):
    """
    Decode a JWT token and return the matching user.

    Verifies the signature (so a forged token is rejected) and the expiry
    (so an old token stops working). Used to protect routes that accept a
    Bearer token instead of an API key.

    Args:
        token (str): The JWT sent by the client in the
            `Authorization: Bearer <token>` header.
        db (Session): An open SQLAlchemy database session.

    Returns:
        models.User: The user the token belongs to.

    Raises:
        HTTPException (401): If the token is missing the username, has a
            bad signature, has expired, or the user no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_user_by_api_key(api_key: str = Depends(api_key_header), db: Session = Depends(get_db)):
    """
    FastAPI dependency that identifies the current user from their API key.

    This is the most-used auth function in the project. Almost every
    endpoint in `main.py` declares `current_user = Depends(get_current_user_by_api_key)`,
    which tells FastAPI to: read the `X-API-Key` header, look the user up,
    and inject the `User` object into the handler — or return 401/403
    automatically if the key is missing, invalid, or the account is disabled.

    Args:
        api_key (str): The value of the `X-API-Key` HTTP header (injected
            automatically by FastAPI via `api_key_header`).
        db (Session): An open database session (injected via `get_db`).

    Returns:
        models.User: The authenticated user object.

    Raises:
        HTTPException (401): No API key header, or key not found in DB.
        HTTPException (403): Account exists but `is_active` is False.

    Example:
        # In a route handler:
        @app.get("/automations")
        async def list_automations(current_user = Depends(get_current_user_by_api_key)):
            # current_user is guaranteed to be a valid, active User here
            ...
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"X-API-Key": "required"},
        )

    user = db.query(models.User).filter(models.User.api_key == api_key).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user
