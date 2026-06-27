"""Feed service gRPC handler."""

from chirp_api.db import SessionLocal
from chirp_api.generated import common_pb2, feed_pb2_grpc, posts_pb2
from chirp_api.middleware.auth import validate_session_token
from chirp_api.services.feed_service import get_explore_feed, get_home_feed
from chirp_api.services.utils import to_proto_timestamp


def to_post_response(post):
    """Convert a post dict from the service layer to a PostResponse proto."""
    assert post is not None, "Post dict must not be None"

    author = post.get("author")
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

    return posts_pb2.PostResponse(
        id=post["id"],
        content=post["content"],
        created_at=to_proto_timestamp(post["created_at"]),
        updated_at=to_proto_timestamp(post["updated_at"]),
        author=author_proto,
        like_count=post.get("like_count") or 0,
        comment_count=post.get("comment_count") or 0,
        is_liked=post.get("is_liked") or False,
    )


class FeedServiceServicer(feed_pb2_grpc.FeedServiceServicer):
    """Handles feed RPCs."""

    def GetHomeFeed(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        # No try/except — let errors propagate as gRPC exceptions
        auth = validate_session_token(request.session_token)

        pagination = request.pagination
        limit = pagination.limit if pagination and pagination.limit else 20
        offset = pagination.offset if pagination and pagination.offset else 0

        with SessionLocal() as session:
            posts = get_home_feed(session, auth["user_id"], limit=limit, offset=offset)

            return posts_pb2.PostsResponse(
                posts=[to_post_response(post) for post in posts],
            )

    def GetExploreFeed(self, request, context):
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

        pagination = request.pagination
        limit = pagination.limit if pagination and pagination.limit else 20
        offset = pagination.offset if pagination and pagination.offset else 0

        with SessionLocal() as session:
            posts = get_explore_feed(session, limit=limit, offset=offset, user_id=user_id)

            return posts_pb2.PostsResponse(
                posts=[to_post_response(post) for post in posts],
            )
