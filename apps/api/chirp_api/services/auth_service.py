"""Authentication service for Chirp API.

Handles user registration, login, and current user retrieval.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from chirp_api.db.models import User
from chirp_api.middleware.auth import create_session_token
from chirp_api.services.utils import generate_id, hash_password, verify_password


def register_user(
    session: Session, email: str, username: str, display_name: str, password: str
) -> dict:
    """Register a new user.

    Returns dict with user_id and session_token.
    Raises Exception if email or username already taken.
    """
    assert isinstance(email, str) and len(email) > 0, "Email must be a non-empty string"
    assert isinstance(username, str) and len(username) > 0, "Username must be a non-empty string"
    assert (
        isinstance(display_name, str) and len(display_name) > 0
    ), "Display name must be a non-empty string"
    assert isinstance(password, str) and len(password) > 0, "Password must be a non-empty string"

    # Check if email already exists
    existing_email = session.execute(select(User).where(User.email == email)).scalar_one_or_none()

    if existing_email:
        raise Exception("User with this email already exists")

    # Check if username already exists
    existing_username = session.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()

    if existing_username:
        raise Exception("Username already taken")

    # Hash password with bcrypt and create user
    password_hash = hash_password(password)
    user_id = generate_id()

    user = User(
        id=user_id,
        email=email,
        username=username,
        display_name=display_name,
        password_hash=password_hash,
        role="user",
    )
    session.add(user)
    session.commit()

    # Create session token
    session_token = create_session_token(user_id, username, "user")

    return {"user_id": user_id, "session_token": session_token}


def login_user(session: Session, email: str, password: str) -> dict:
    """Login user by email and password.

    Returns dict with user_id and session_token.
    Raises Exception if credentials invalid or user banned.

    Migration: if the stored hash is the legacy SHA-256 format, verifies
    against the old scheme and transparently rehashes to bcrypt on success.
    """
    assert isinstance(email, str) and len(email) > 0, "Email must be a non-empty string"
    assert isinstance(password, str) and len(password) > 0, "Password must be a non-empty string"

    # Find user by email
    user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()

    if not user:
        raise Exception("Invalid email or password")

    # Check if user is banned
    if user.banned_at:
        reason = user.banned_reason or "No reason provided"
        raise Exception(f"Account banned: {reason}")

    # Verify password (handles both legacy SHA-256 and bcrypt)
    if not verify_password(password, user.password_hash):
        raise Exception("Invalid email or password")

    # Migrate legacy SHA-256 hash to bcrypt on first successful login
    from chirp_api.services.utils import _is_legacy_hash
    if _is_legacy_hash(user.password_hash):
        user.password_hash = hash_password(password)
        session.commit()

    # Create session token
    session_token = create_session_token(user.id, user.username, user.role)

    return {"user_id": user.id, "session_token": session_token}


def get_current_user(session: Session, user_id: str) -> dict:
    """Get current user profile by ID.

    Returns dict with user fields.
    Raises Exception if user not found.
    """
    assert isinstance(user_id, str) and len(user_id) > 0, "user_id must be a non-empty string"

    user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    if not user:
        raise Exception("User not found")

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "role": user.role,
        "created_at": user.created_at,
    }
