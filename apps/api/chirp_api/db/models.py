"""SQLAlchemy 2.0 ORM models for Chirp API.

Mirrors the Drizzle schema from 0000_thankful_polaris.sql exactly.
All IDs are text (string). All timestamps are integer (unix epoch).
"""

import time

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _unix_epoch() -> int:
    return int(time.time())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="user")
    banned_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    banned_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    banned_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=_unix_epoch)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False, default=_unix_epoch)


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=_unix_epoch)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False, default=_unix_epoch)


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    post_id: Mapped[str] = mapped_column(
        Text, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=_unix_epoch)


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="likes_user_id_post_id_unique"),
        UniqueConstraint("user_id", "comment_id", name="likes_user_id_comment_id_unique"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    post_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("posts.id", ondelete="CASCADE"), nullable=True
    )
    comment_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=_unix_epoch)


class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint(
            "follower_id", "following_id", name="follows_follower_id_following_id_unique"
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    follower_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    following_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=_unix_epoch)


class Bookmark(Base):
    __tablename__ = "bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="bookmarks_user_id_post_id_unique"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    post_id: Mapped[str] = mapped_column(
        Text, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=_unix_epoch)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    post_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("posts.id", ondelete="CASCADE"), nullable=True
    )
    comment_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=_unix_epoch)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    reporter_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    target_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    reviewed_by: Mapped[str | None] = mapped_column(
        Text, ForeignKey("users.id", ondelete="NO ACTION"), nullable=True
    )
    reviewed_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=_unix_epoch)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    admin_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=_unix_epoch)
