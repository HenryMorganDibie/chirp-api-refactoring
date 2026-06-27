"""Tests for follows_service — follow toggle, status, and counts.

Uses real in-memory database via the session fixture. No mocking.
"""

import pytest

from chirp_api.services.follows_service import (
    get_follow_status,
    get_follower_count,
    get_following_count,
    toggle_follow,
)
from tests.helpers import create_test_user


class TestToggleFollow:
    def test_toggle_follow_on(self, session):
        user1 = create_test_user(session)
        user2 = create_test_user(session)

        result = toggle_follow(session, username=user2.username, follower_id=user1.id)

        assert result["following"] is True

    def test_toggle_follow_off(self, session):
        user1 = create_test_user(session)
        user2 = create_test_user(session)

        # Follow
        toggle_follow(session, username=user2.username, follower_id=user1.id)
        # Unfollow
        result = toggle_follow(session, username=user2.username, follower_id=user1.id)

        assert result["following"] is False

    def test_prevent_self_follow(self, session):
        user = create_test_user(session)

        with pytest.raises(Exception, match="cannot follow yourself"):
            toggle_follow(session, username=user.username, follower_id=user.id)


class TestGetFollowStatus:
    def test_get_follow_status(self, session):
        user1 = create_test_user(session)
        user2 = create_test_user(session)

        # Not following yet
        result = get_follow_status(session, username=user2.username, follower_id=user1.id)
        assert result["following"] is False

        # Follow
        toggle_follow(session, username=user2.username, follower_id=user1.id)

        # Now following
        result = get_follow_status(session, username=user2.username, follower_id=user1.id)
        assert result["following"] is True


class TestFollowCounts:
    def test_get_follower_count(self, session):
        user1 = create_test_user(session)
        user2 = create_test_user(session)
        user3 = create_test_user(session)

        toggle_follow(session, username=user1.username, follower_id=user2.id)
        toggle_follow(session, username=user1.username, follower_id=user3.id)

        result = get_follower_count(session, username=user1.username)
        assert result["count"] == 2

    def test_get_following_count(self, session):
        user1 = create_test_user(session)
        user2 = create_test_user(session)
        user3 = create_test_user(session)

        toggle_follow(session, username=user2.username, follower_id=user1.id)
        toggle_follow(session, username=user3.username, follower_id=user1.id)

        result = get_following_count(session, username=user1.username)
        assert result["count"] == 2
