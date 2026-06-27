"""Comments service gRPC handler.

Consistent error handling: all methods return error responses on failure.
"""

from chirp_api.db import SessionLocal
from chirp_api.generated import comments_pb2, comments_pb2_grpc, common_pb2
from chirp_api.middleware.auth import validate_session_token
from chirp_api.services.comments_service import (
    create_comment,
    delete_comment,
    get_post_comments,
)
from chirp_api.services.utils import to_proto_timestamp

# Maximum recursion depth for nested comment replies.
# Prevents stack overflow from deeply nested reply chains.
COMMENT_REPLY_DEPTH_LIMIT = 10


def to_comment_response(comment, depth=0):
    """Convert a comment dict from the service layer to a CommentResponse proto.

    Handles recursive replies up to COMMENT_REPLY_DEPTH_LIMIT levels deep.
    """
    assert comment is not None, "Comment dict must not be None"
    assert depth >= 0, "Depth must not be negative"
    assert (
        depth <= COMMENT_REPLY_DEPTH_LIMIT
    ), f"Comment nesting depth {depth} exceeds limit {COMMENT_REPLY_DEPTH_LIMIT}"

    author = comment.get("author")
    if author:
        author_proto = common_pb2.Author(
            id=author.get("id") or "",
            username=author.get("username") or "",
            display_name=author.get("display_name") or "",
            avatar_url=author.get("avatar_url") or "",
        )
    else:
        author_proto = common_pb2.Author(
            id="",
            username="",
            display_name="",
        )

    # Convert replies iteratively with depth limit
    replies = comment.get("replies") or []
    if depth < COMMENT_REPLY_DEPTH_LIMIT:
        reply_protos = [to_comment_response(reply, depth + 1) for reply in replies]
    else:
        reply_protos = []

    return comments_pb2.CommentResponse(
        id=comment["id"],
        content=comment["content"],
        created_at=to_proto_timestamp(comment["created_at"]),
        parent_id=comment.get("parent_id") or "",
        author=author_proto,
        like_count=comment.get("like_count") or 0,
        is_liked=comment.get("is_liked") or False,
        replies=reply_protos,
    )


class CommentsServiceServicer(comments_pb2_grpc.CommentsServiceServicer):
    """Handles comment RPCs."""

    def CreateComment(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                result = create_comment(
                    session,
                    post_id=request.post_id,
                    content=request.content,
                    author_id=auth["user_id"],
                    parent_id=request.parent_id or None,
                )

                return comments_pb2.CreateCommentResponse(
                    success=True,
                    comment_id=result["comment_id"],
                )
        except Exception as error:
            return comments_pb2.CreateCommentResponse(
                success=False,
                comment_id="",
                error=str(error),
            )

    def GetPostComments(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        user_id = None
        if request.session_token:
            try:
                auth = validate_session_token(request.session_token)
                user_id = auth["user_id"]
            except Exception:
                # Ignore invalid token for public access
                pass

        with SessionLocal() as session:
            comments = get_post_comments(session, request.post_id, user_id)

            return comments_pb2.CommentsResponse(
                comments=[to_comment_response(comment) for comment in comments],
            )

    def DeleteComment(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                delete_comment(session, request.comment_id, auth["user_id"])

                return comments_pb2.DeleteCommentResponse(success=True)
        except Exception as error:
            return comments_pb2.DeleteCommentResponse(
                success=False,
                error=str(error),
            )
