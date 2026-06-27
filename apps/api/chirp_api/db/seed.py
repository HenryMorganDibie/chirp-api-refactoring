"""Seed data for Chirp API database.

Mirrors the TypeScript seed exactly: 7 users, 8 posts, 8 comments, 17 likes, 9 follows.
Uses INSERT OR IGNORE for idempotency.
"""

import os
import sqlite3
import sys

# Ensure the package is importable when run as a module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from chirp_api.db import engine
from chirp_api.db.models import Base
from chirp_api.services.utils import generate_id, hash_password


def seed():
    """Seed the database with test data."""
    print("Seeding database...")

    # Create tables if they don't exist
    Base.metadata.create_all(engine)

    # Use raw sqlite3 connection for INSERT OR IGNORE
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./chirp.db")
    db_path = database_url.replace("sqlite:///", "")
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # --- Users ---
    test_users = [
        {
            "id": generate_id(),
            "email": "alice@test.com",
            "username": "alice",
            "display_name": "Alice Johnson",
            "password": "password123",
            "role": "user",
            "bio": "Coffee enthusiast \u2615 | Developer | Love to share thoughts",
        },
        {
            "id": generate_id(),
            "email": "bob@test.com",
            "username": "bob",
            "display_name": "Bob Smith",
            "password": "password123",
            "role": "user",
            "bio": "Just a guy who loves coding",
        },
        {
            "id": generate_id(),
            "email": "charlie@test.com",
            "username": "charlie",
            "display_name": "Charlie Brown",
            "password": "password123",
            "role": "user",
            "bio": "Living life one day at a time",
        },
        {
            "id": generate_id(),
            "email": "diana@test.com",
            "username": "diana",
            "display_name": "Diana Ross",
            "password": "password123",
            "role": "user",
            "bio": "Music is my soul",
        },
        {
            "id": generate_id(),
            "email": "admin@test.com",
            "username": "admin_old",
            "display_name": "Admin User Old",
            "password": "admin123",
            "role": "admin",
            "bio": "System administrator",
        },
        {
            "id": generate_id(),
            "email": "admin@chirp.test",
            "username": "admin",
            "display_name": "Admin User",
            "password": "admin123",
            "role": "admin",
            "bio": "Platform administrator",
        },
        {
            "id": generate_id(),
            "email": "moderator@chirp.test",
            "username": "moderator",
            "display_name": "Moderator User",
            "password": "mod123",
            "role": "moderator",
            "bio": "Content moderator",
        },
    ]

    for user in test_users:
        password_hash = hash_password(user["password"])
        cursor.execute(
            """INSERT OR IGNORE INTO users
               (id, email, username, display_name, password_hash, role, bio, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, strftime('%s','now'), strftime('%s','now'))""",
            (
                user["id"],
                user["email"],
                user["username"],
                user["display_name"],
                password_hash,
                user["role"],
                user["bio"],
            ),
        )
        print(f"Created user: {user['username']}")

    alice = test_users[0]
    bob = test_users[1]
    charlie = test_users[2]
    diana = test_users[3]

    # --- Posts ---
    post1_id = generate_id()
    post2_id = generate_id()
    post3_id = generate_id()
    post4_id = generate_id()
    post5_id = generate_id()
    post6_id = generate_id()
    post7_id = generate_id()
    post8_id = generate_id()

    posts_data = [
        (
            post1_id,
            "Just deployed my first full-stack app with gRPC and TypeScript. The type safety across the entire stack is incredible!",
            alice["id"],
        ),
        (
            post2_id,
            "Morning coffee and code reviews. There is something peaceful about reading clean, well-structured code early in the day.",
            bob["id"],
        ),
        (
            post3_id,
            "Hot take: monorepos are the way to go for any team project. Shared packages, consistent tooling, and atomic changes across services.",
            alice["id"],
        ),
        (
            post4_id,
            "Finally wrapped my head around Protocol Buffers. The schema-first approach to API design changes everything.",
            charlie["id"],
        ),
        (
            post5_id,
            "Spent the weekend learning StyleX. CSS-in-JS with zero runtime cost? Sign me up.",
            diana["id"],
        ),
        (
            post6_id,
            "Pair programming tip: the navigator should think about the big picture while the driver focuses on implementation details. Works every time.",
            bob["id"],
        ),
        (
            post7_id,
            "TIL that TanStack Router has file-based routing with full type safety. No more guessing route params!",
            charlie["id"],
        ),
        (
            post8_id,
            "Music recommendation for coding: lo-fi beats are great, but have you tried ambient soundscapes? Total game changer for deep focus.",
            diana["id"],
        ),
    ]

    for post_id, content, author_id in posts_data:
        cursor.execute(
            """INSERT OR IGNORE INTO posts
               (id, content, author_id, created_at, updated_at)
               VALUES (?, ?, ?, strftime('%s','now'), strftime('%s','now'))""",
            (post_id, content, author_id),
        )
    print("Created sample posts")

    # --- Comments ---
    comments_data = [
        (
            generate_id(),
            "Congrats on the deployment! What was the trickiest part of the gRPC setup?",
            post1_id,
            bob["id"],
        ),
        (
            generate_id(),
            "The type safety with Protobuf + TypeScript is next level. Welcome to the club!",
            post1_id,
            charlie["id"],
        ),
        (
            generate_id(),
            "Could not agree more. A good codebase is a joy to read.",
            post2_id,
            alice["id"],
        ),
        (
            generate_id(),
            "Totally agree! We switched to a monorepo last year and never looked back.",
            post3_id,
            diana["id"],
        ),
        (
            generate_id(),
            "Check out Buf for linting and managing your proto files. It is a huge time saver.",
            post4_id,
            alice["id"],
        ),
        (
            generate_id(),
            "StyleX is amazing! The compile-time optimization makes such a difference in bundle size.",
            post5_id,
            bob["id"],
        ),
        (
            generate_id(),
            "Great tip! I always struggle with knowing when to step back as the driver.",
            post6_id,
            charlie["id"],
        ),
        (
            generate_id(),
            'I love ambient soundscapes for coding! Check out the "A Soft Murmur" website.',
            post8_id,
            alice["id"],
        ),
    ]

    for comment_id, content, post_id, author_id in comments_data:
        cursor.execute(
            """INSERT OR IGNORE INTO comments
               (id, content, post_id, author_id, created_at)
               VALUES (?, ?, ?, ?, strftime('%s','now'))""",
            (comment_id, content, post_id, author_id),
        )
    print("Created sample comments")

    # --- Likes ---
    likes_data = [
        (generate_id(), bob["id"], post1_id),
        (generate_id(), charlie["id"], post1_id),
        (generate_id(), diana["id"], post1_id),
        (generate_id(), alice["id"], post2_id),
        (generate_id(), charlie["id"], post2_id),
        (generate_id(), bob["id"], post3_id),
        (generate_id(), diana["id"], post3_id),
        (generate_id(), alice["id"], post4_id),
        (generate_id(), bob["id"], post4_id),
        (generate_id(), alice["id"], post5_id),
        (generate_id(), charlie["id"], post5_id),
        (generate_id(), alice["id"], post6_id),
        (generate_id(), diana["id"], post6_id),
        (generate_id(), bob["id"], post7_id),
        (generate_id(), diana["id"], post7_id),
        (generate_id(), bob["id"], post8_id),
        (generate_id(), charlie["id"], post8_id),
    ]

    for like_id, user_id, post_id in likes_data:
        cursor.execute(
            """INSERT OR IGNORE INTO likes
               (id, user_id, post_id, created_at)
               VALUES (?, ?, ?, strftime('%s','now'))""",
            (like_id, user_id, post_id),
        )
    print("Created sample likes")

    # --- Follows ---
    follows_data = [
        (generate_id(), bob["id"], alice["id"]),
        (generate_id(), charlie["id"], alice["id"]),
        (generate_id(), diana["id"], alice["id"]),
        (generate_id(), alice["id"], bob["id"]),
        (generate_id(), charlie["id"], bob["id"]),
        (generate_id(), alice["id"], charlie["id"]),
        (generate_id(), bob["id"], charlie["id"]),
        (generate_id(), alice["id"], diana["id"]),
        (generate_id(), bob["id"], diana["id"]),
    ]

    for follow_id, follower_id, following_id in follows_data:
        cursor.execute(
            """INSERT OR IGNORE INTO follows
               (id, follower_id, following_id, created_at)
               VALUES (?, ?, ?, strftime('%s','now'))""",
            (follow_id, follower_id, following_id),
        )
    print("Created sample follows")

    connection.commit()
    connection.close()
    print("Database seeded successfully!")


if __name__ == "__main__":
    seed()
