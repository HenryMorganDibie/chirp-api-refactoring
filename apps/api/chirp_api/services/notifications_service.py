"""Notifications service for Chirp API."""

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from chirp_api.db.models import Comment, Notification, Post, User
from chirp_api.services.utils import generate_id


def create_notification(
    session: Session,
    user_id: str,
    notification_type: str,
    actor_id: str,
    post_id: str | None = None,
    comment_id: str | None = None,
) -> dict | None:
    """Create a notification.

    Returns dict with notification_id, or None if self-notification (skipped).
    """
    # Don't notify users about their own actions
    if user_id == actor_id:
        return None

    notification_id = generate_id()
    notification = Notification(
        id=notification_id,
        user_id=user_id,
        type=notification_type,
        actor_id=actor_id,
        post_id=post_id or None,
        comment_id=comment_id or None,
    )
    session.add(notification)
    session.commit()

    return {"notification_id": notification_id}


def get_user_notifications(
    session: Session,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> list:
    """Get notifications for a user with pagination.

    Returns list of notification dicts.
    """
    assert isinstance(user_id, str) and len(user_id) > 0, "user_id must be non-empty"
    assert limit > 0 and limit <= 100, "Limit must be between 1 and 100"
    assert offset >= 0, "Offset must be non-negative"

    results = session.execute(
        select(Notification, User)
        .outerjoin(User, Notification.actor_id == User.id)
        .where(Notification.user_id == user_id)
        .order_by(desc(Notification.created_at))
        .limit(limit)
        .offset(offset)
    ).all()

    enriched_results = []
    for notification, actor in results:
        post_content = None
        comment_content = None

        # Query per notification for post content
        if notification.post_id:
            post = session.execute(
                select(Post.content).where(Post.id == notification.post_id)
            ).scalar_one_or_none()
            if post:
                post_content = post[:100] if len(post) > 100 else post

        # Query per notification for comment content
        if notification.comment_id:
            comment = session.execute(
                select(Comment.content).where(Comment.id == notification.comment_id)
            ).scalar_one_or_none()
            if comment:
                comment_content = comment[:100] if len(comment) > 100 else comment

        enriched_results.append(
            {
                "id": notification.id,
                "type": notification.type,
                "read": notification.read,
                "created_at": notification.created_at,
                "post_id": notification.post_id,
                "comment_id": notification.comment_id,
                "actor": {
                    "id": actor.id if actor else None,
                    "username": actor.username if actor else None,
                    "display_name": actor.display_name if actor else None,
                    "avatar_url": actor.avatar_url if actor else None,
                },
                "post_content": post_content,
                "comment_content": comment_content,
            }
        )

    return enriched_results


def get_unread_count(session: Session, user_id: str) -> dict:
    """Get unread notification count for a user.

    Returns dict with count integer.
    """
    count = (
        session.execute(
            select(func.count())
            .select_from(Notification)
            .where(and_(Notification.user_id == user_id, Notification.read == False))  # noqa: E712
        ).scalar()
        or 0
    )

    return {"count": count}


def mark_as_read(session: Session, notification_id: str, user_id: str) -> dict:
    """Mark a single notification as read.

    Returns dict with success boolean.
    Raises Exception if notification not found or not owned by user.
    """
    notification = session.execute(
        select(Notification).where(Notification.id == notification_id)
    ).scalar_one_or_none()

    if not notification:
        raise Exception("Notification not found")

    if notification.user_id != user_id:
        raise Exception("Unauthorized")

    notification.read = True
    session.commit()

    return {"success": True}


def mark_all_as_read(session: Session, user_id: str) -> dict:
    """Mark all notifications as read for a user.

    Returns dict with success boolean.
    """
    from sqlalchemy import update

    session.execute(update(Notification).where(Notification.user_id == user_id).values(read=True))
    session.commit()

    return {"success": True}


def delete_notification(session: Session, notification_id: str, user_id: str) -> dict:
    """Delete a notification.

    Returns dict with success boolean.
    Raises Exception if notification not found or not owned by user.
    """
    notification = session.execute(
        select(Notification).where(Notification.id == notification_id)
    ).scalar_one_or_none()

    if not notification:
        raise Exception("Notification not found")

    if notification.user_id != user_id:
        raise Exception("Unauthorized")

    session.delete(notification)
    session.commit()

    return {"success": True}
