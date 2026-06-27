"""Utility functions for Chirp API services.

Contains ID generation, password hashing, and timestamp conversion.

SECURITY NOTE (Issue 1 — Credential Problem):
  Previously used SHA-256 with a hardcoded static salt ("salt"). This is
  critically insecure: SHA-256 is a fast general-purpose hash, not a
  password KDF. A static salt means every identical password produces an
  identical hash, enabling precomputed rainbow-table and batch brute-force
  attacks. An attacker with the database could crack all passwords offline
  in hours using commodity hardware.

  Fix: bcrypt with per-password random salts and a cost factor of 12.
  bcrypt is deliberately slow (~100ms/attempt), making brute-force
  computationally infeasible.

  Backwards-compatibility migration strategy:
  - Existing seeded users have SHA-256 hashes (64 hex chars, no "$2b$" prefix).
  - On login, if the stored hash is a legacy SHA-256 hash, verify against
    the old algorithm. On success, immediately rehash with bcrypt and persist.
  - New registrations always use bcrypt.
  - This "on-login rehash" approach migrates users transparently without
    requiring plaintext passwords or a forced reset.
"""

import hashlib
import random
import string
import time

import bcrypt


def generate_id() -> str:
    """Generate a simple unique ID: timestamp-random."""
    timestamp = int(time.time() * 1000)
    random_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    result = f"{timestamp}-{random_str}"
    assert len(result) > 0, "Generated ID must not be empty"
    return result


def _is_legacy_hash(hashed: str) -> bool:
    """Return True if the stored hash is the old SHA-256 hex format.

    Legacy hashes are 64-character hex strings.
    bcrypt hashes start with '$2b$' and are longer.
    """
    return len(hashed) == 64 and not hashed.startswith("$2b$")


def _legacy_hash(password: str) -> str:
    """Reproduce the old insecure SHA-256 hash for migration verification only."""
    return hashlib.sha256((password + "salt").encode()).hexdigest()


def hash_password(password: str) -> str:
    """Hash password using bcrypt with a per-password random salt."""
    assert isinstance(password, str), "Password must be a string"
    assert len(password) > 0, "Password must not be empty"
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against stored hash.

    Supports both bcrypt (new) and legacy SHA-256 (old) hashes transparently.
    Callers should rehash with hash_password() on successful legacy verification.
    """
    assert isinstance(password, str), "Password must be a string"
    assert isinstance(hashed, str), "Hash must be a string"

    if _is_legacy_hash(hashed):
        # Legacy path: verify with old SHA-256 scheme
        return _legacy_hash(password) == hashed

    # Modern path: verify with bcrypt
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def to_proto_timestamp(dt):
    """Convert datetime or unix timestamp int to proto Timestamp message."""
    from chirp_api.generated import common_pb2

    if dt is None:
        return common_pb2.Timestamp(seconds=0, nanos=0)
    if isinstance(dt, int):
        return common_pb2.Timestamp(seconds=dt, nanos=0)
    return common_pb2.Timestamp(seconds=int(dt.timestamp()), nanos=0)
