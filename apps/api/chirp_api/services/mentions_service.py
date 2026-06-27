"""Mentions service for Chirp API.

Extracts @username mentions from content, validates them, and creates notifications.
"""

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from chirp_api.db.models import User
from chirp_api.services.notifications_service import create_notification


def extract_mentions(content: str) -> list[str]:
    """Extract @usernames from content.

    Returns unique list of usernames (without the @ symbol).
    """
    assert isinstance(content, str), "Content must be a string"

    mention_pattern = r"@([a-zA-Z0-9_]+)"
    matches = re.findall(mention_pattern, content)
    # Deduplicate while preserving order
    seen = set()
    unique_usernames = []
    for username in matches:
        if username not in seen:
            seen.add(username)
            unique_usernames.append(username)
    return unique_usernames


def validate_mentioned_users(session: Session, usernames: list[str]) -> dict[str, str]:
    """Validate that mentioned usernames exist in the database.

    Returns dict mapping username to userId for valid users.
    """
    if len(usernames) == 0:
        return {}

    users = session.execute(
        select(User.id, User.username).where(User.username.in_(usernames))
    ).all()

    username_to_id = {}
    for user_id, username in users:
        username_to_id[username] = user_id

    return username_to_id


def create_mention_notifications(
    session: Session,
    mentioned_user_ids: list[str],
    actor_id: str,
    post_id: str | None = None,
    comment_id: str | None = None,
) -> None:
    """Create notifications for mentioned users.

    Skips self-mentions (actor mentioning themselves).
    """
    # Filter out self-mentions
    user_ids_to_notify = [uid for uid in mentioned_user_ids if uid != actor_id]

    for user_id in user_ids_to_notify:
        create_notification(
            session,
            user_id=user_id,
            notification_type="mention",
            actor_id=actor_id,
            post_id=post_id,
            comment_id=comment_id,
        )


def process_mentions(
    session: Session,
    content: str,
    actor_id: str,
    post_id: str | None = None,
    comment_id: str | None = None,
) -> None:
    """Process mentions in content: extract, validate, and create notifications.

    Helper that combines all mention-related operations.
    """
    mentioned_usernames = extract_mentions(content)

    if len(mentioned_usernames) == 0:
        return

    valid_users = validate_mentioned_users(session, mentioned_usernames)
    mentioned_user_ids = list(valid_users.values())

    if len(mentioned_user_ids) > 0:
        create_mention_notifications(session, mentioned_user_ids, actor_id, post_id, comment_id)
