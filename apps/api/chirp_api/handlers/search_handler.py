"""Search service gRPC handler.

Consistent error handling.
"""

from chirp_api.db import SessionLocal
from chirp_api.generated import common_pb2, posts_pb2, search_pb2, search_pb2_grpc
from chirp_api.middleware.auth import validate_session_token
from chirp_api.services.search_service import search_posts, search_users
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


class SearchServiceServicer(search_pb2_grpc.SearchServiceServicer):
    """Handles search RPCs."""

    def SearchPosts(self, request, context):
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
            posts = search_posts(session, request.query, user_id)

            return posts_pb2.PostsResponse(
                posts=[to_post_response(post) for post in posts],
            )

    def SearchUsers(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        with SessionLocal() as session:
            users = search_users(session, request.query)

            return search_pb2.UsersResponse(
                users=[
                    search_pb2.UserSearchResult(
                        id=user["id"],
                        username=user["username"],
                        display_name=user["display_name"],
                        avatar_url=user.get("avatar_url") or "",
                        bio=user.get("bio") or "",
                    )
                    for user in users
                ],
            )
