"""Follows service gRPC handler."""

from chirp_api.db import SessionLocal
from chirp_api.generated import follows_pb2, follows_pb2_grpc
from chirp_api.middleware.auth import validate_session_token
from chirp_api.services.follows_service import (
    get_follow_status,
    get_follower_count,
    get_following_count,
    toggle_follow,
)


class FollowsServiceServicer(follows_pb2_grpc.FollowsServiceServicer):
    """Handles follow/unfollow and status RPCs."""

    def ToggleFollow(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                result = toggle_follow(session, request.username, auth["user_id"])

                return follows_pb2.FollowResponse(
                    success=True,
                    following=result["following"],
                )
        except Exception as error:
            return follows_pb2.FollowResponse(
                success=False,
                following=False,
                error=str(error),
            )

    def GetFollowStatus(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                result = get_follow_status(session, request.username, auth["user_id"])

                return follows_pb2.FollowStatusResponse(following=result["following"])
        except Exception:
            return follows_pb2.FollowStatusResponse(following=False)

    def GetFollowerCount(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            with SessionLocal() as session:
                result = get_follower_count(session, request.username)

                return follows_pb2.CountResponse(count=result["count"])
        except Exception:
            return follows_pb2.CountResponse(count=0)

    def GetFollowingCount(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            with SessionLocal() as session:
                result = get_following_count(session, request.username)

                return follows_pb2.CountResponse(count=result["count"])
        except Exception:
            return follows_pb2.CountResponse(count=0)
