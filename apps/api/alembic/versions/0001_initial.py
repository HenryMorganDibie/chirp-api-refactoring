"""Initial schema - all tables.

Revision ID: 0001
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table must be created first (referenced by all others)
    op.execute("""
        CREATE TABLE users (
            id text PRIMARY KEY NOT NULL,
            email text NOT NULL,
            username text NOT NULL,
            display_name text NOT NULL,
            avatar_url text,
            bio text,
            password_hash text NOT NULL,
            role text DEFAULT 'user' NOT NULL,
            banned_at integer,
            banned_reason text,
            banned_by text,
            created_at integer DEFAULT (unixepoch()) NOT NULL,
            updated_at integer DEFAULT (unixepoch()) NOT NULL
        )
    """)
    op.execute("CREATE UNIQUE INDEX users_email_unique ON users (email)")
    op.execute("CREATE UNIQUE INDEX users_username_unique ON users (username)")

    op.execute("""
        CREATE TABLE posts (
            id text PRIMARY KEY NOT NULL,
            content text NOT NULL,
            author_id text NOT NULL,
            created_at integer DEFAULT (unixepoch()) NOT NULL,
            updated_at integer DEFAULT (unixepoch()) NOT NULL,
            FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE cascade
        )
    """)

    op.execute("""
        CREATE TABLE comments (
            id text PRIMARY KEY NOT NULL,
            content text NOT NULL,
            post_id text NOT NULL,
            author_id text NOT NULL,
            parent_id text,
            created_at integer DEFAULT (unixepoch()) NOT NULL,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE cascade,
            FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE cascade,
            FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE cascade
        )
    """)

    op.execute("""
        CREATE TABLE likes (
            id text PRIMARY KEY NOT NULL,
            user_id text NOT NULL,
            post_id text,
            comment_id text,
            created_at integer DEFAULT (unixepoch()) NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE cascade,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE cascade,
            FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE cascade
        )
    """)
    op.execute("CREATE UNIQUE INDEX likes_user_id_post_id_unique ON likes (user_id, post_id)")
    op.execute("CREATE UNIQUE INDEX likes_user_id_comment_id_unique ON likes (user_id, comment_id)")

    op.execute("""
        CREATE TABLE follows (
            id text PRIMARY KEY NOT NULL,
            follower_id text NOT NULL,
            following_id text NOT NULL,
            created_at integer DEFAULT (unixepoch()) NOT NULL,
            FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE cascade,
            FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE cascade
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX follows_follower_id_following_id_unique ON follows (follower_id, following_id)"
    )

    op.execute("""
        CREATE TABLE bookmarks (
            id text PRIMARY KEY NOT NULL,
            user_id text NOT NULL,
            post_id text NOT NULL,
            created_at integer DEFAULT (unixepoch()) NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE cascade,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE cascade
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX bookmarks_user_id_post_id_unique ON bookmarks (user_id, post_id)"
    )

    op.execute("""
        CREATE TABLE notifications (
            id text PRIMARY KEY NOT NULL,
            user_id text NOT NULL,
            type text NOT NULL,
            actor_id text NOT NULL,
            post_id text,
            comment_id text,
            read integer DEFAULT 0 NOT NULL,
            created_at integer DEFAULT (unixepoch()) NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE cascade,
            FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE cascade,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE cascade,
            FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE cascade
        )
    """)

    op.execute("""
        CREATE TABLE reports (
            id text PRIMARY KEY NOT NULL,
            reporter_id text NOT NULL,
            target_type text NOT NULL,
            target_id text NOT NULL,
            reason text NOT NULL,
            description text,
            status text DEFAULT 'pending' NOT NULL,
            reviewed_by text,
            reviewed_at integer,
            created_at integer DEFAULT (unixepoch()) NOT NULL,
            FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE cascade,
            FOREIGN KEY (reviewed_by) REFERENCES users(id)
        )
    """)

    op.execute("""
        CREATE TABLE audit_logs (
            id text PRIMARY KEY NOT NULL,
            admin_id text NOT NULL,
            action text NOT NULL,
            target_type text,
            target_id text,
            details text,
            ip_address text,
            created_at integer DEFAULT (unixepoch()) NOT NULL,
            FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE cascade
        )
    """)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("reports")
    op.drop_table("notifications")
    op.drop_table("bookmarks")
    op.drop_table("follows")
    op.drop_table("likes")
    op.drop_table("comments")
    op.drop_table("posts")
    op.drop_table("users")
