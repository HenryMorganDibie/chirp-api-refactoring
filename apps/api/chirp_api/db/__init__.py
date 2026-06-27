"""Database engine and session factory for Chirp API.

Uses SQLAlchemy 2.0 with sync engine and SQLite.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./chirp.db")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
