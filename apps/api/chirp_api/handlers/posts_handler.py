"""Posts service gRPC handler.

Consistent error handling: all methods return error responses on failure.
"""

from chirp_api.db import SessionLocal
from chirp_api.generated import common_pb2, posts_pb2, posts_pb2_grpc
from chirp_api.middleware.auth import validate_session_token
from chirp_api.services.posts_service import (
    create_post,
    delete_post,
    get_post,
    get_posts,
    get_user_posts,
    update_post,
)
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


class PostsServiceServicer(posts_pb2_grpc.PostsServiceServicer):
    """Handles post CRUD RPCs."""

    def CreatePost(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                result = create_post(
                    session,
                    content=request.content,
                    author_id=auth["user_id"],
                )

                return posts_pb2.CreatePostResponse(
                    success=True,
                    post_id=result["post_id"],
                )
        except Exception as error:
            return posts_pb2.CreatePostResponse(
                success=False,
                post_id="",
                error=str(error),
            )

    def GetPost(self, request, context):
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

        try:
            with SessionLocal() as session:
                post = get_post(session, request.post_id, user_id)
                return to_post_response(post)
        except Exception:
            return posts_pb2.PostResponse(
                id="",
                content="",
                author=common_pb2.Author(id="", username="", display_name=""),
            )

    def UpdatePost(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                update_post(
                    session,
                    post_id=request.post_id,
                    content=request.content,
                    user_id=auth["user_id"],
                )

                return posts_pb2.UpdatePostResponse(success=True)
        except Exception as error:
            return posts_pb2.UpdatePostResponse(
                success=False,
                error=str(error),
            )

    def DeletePost(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                delete_post(session, request.post_id, auth["user_id"])

                return posts_pb2.DeletePostResponse(success=True)
        except Exception as error:
            return posts_pb2.DeletePostResponse(
                success=False,
                error=str(error),
            )

    def GetPosts(self, request, context):
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
            posts = get_posts(session, limit=limit, offset=offset, user_id=user_id)

            return posts_pb2.PostsResponse(
                posts=[to_post_response(post) for post in posts],
            )

    def GetUserPosts(self, request, context):
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

        try:
            with SessionLocal() as session:
                posts = get_user_posts(session, request.username, user_id)

                return posts_pb2.PostsResponse(
                    posts=[to_post_response(post) for post in posts],
                )
        except Exception:
            return posts_pb2.PostsResponse(posts=[])
