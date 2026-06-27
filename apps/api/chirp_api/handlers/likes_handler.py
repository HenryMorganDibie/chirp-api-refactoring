"""Likes service gRPC handler."""

from chirp_api.db import SessionLocal
from chirp_api.generated import likes_pb2, likes_pb2_grpc
from chirp_api.middleware.auth import validate_session_token
from chirp_api.services.likes_service import (
    get_comment_like_status,
    get_post_like_status,
    toggle_comment_like,
    toggle_post_like,
)


class LikesServiceServicer(likes_pb2_grpc.LikesServiceServicer):
    """Handles like toggle and status RPCs."""

    def TogglePostLike(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                result = toggle_post_like(session, request.post_id, auth["user_id"])

                return likes_pb2.LikeResponse(
                    success=True,
                    liked=result["liked"],
                )
        except Exception as error:
            return likes_pb2.LikeResponse(
                success=False,
                liked=False,
                error=str(error),
            )

    def ToggleCommentLike(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                result = toggle_comment_like(session, request.comment_id, auth["user_id"])

                return likes_pb2.LikeResponse(
                    success=True,
                    liked=result["liked"],
                )
        except Exception as error:
            return likes_pb2.LikeResponse(
                success=False,
                liked=False,
                error=str(error),
            )

    def GetPostLikeStatus(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                result = get_post_like_status(session, request.post_id, auth["user_id"])

                return likes_pb2.LikeStatusResponse(liked=result["liked"])
        except Exception:
            return likes_pb2.LikeStatusResponse(liked=False)

    def GetCommentLikeStatus(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                result = get_comment_like_status(session, request.comment_id, auth["user_id"])

                return likes_pb2.LikeStatusResponse(liked=result["liked"])
        except Exception:
            return likes_pb2.LikeStatusResponse(liked=False)
