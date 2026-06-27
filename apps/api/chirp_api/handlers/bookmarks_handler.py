"""Bookmarks service gRPC handler.

Consistent error handling: all methods return error responses on failure.
"""

from chirp_api.db import SessionLocal
from chirp_api.generated import bookmarks_pb2, bookmarks_pb2_grpc, common_pb2, posts_pb2
from chirp_api.middleware.auth import validate_session_token
from chirp_api.services.bookmarks_service import (
    get_bookmark_status,
    get_bookmarked_posts,
    toggle_bookmark,
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
        author_proto = None

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


class BookmarksServiceServicer(bookmarks_pb2_grpc.BookmarksServiceServicer):
    """Handles bookmark RPCs."""

    def ToggleBookmark(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                result = toggle_bookmark(session, request.post_id, auth["user_id"])

                return bookmarks_pb2.BookmarkResponse(
                    success=True,
                    bookmarked=result["bookmarked"],
                )
        except Exception as error:
            return bookmarks_pb2.BookmarkResponse(
                success=False,
                bookmarked=False,
                error=str(error),
            )

    def GetBookmarkStatus(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                result = get_bookmark_status(session, request.post_id, auth["user_id"])

                return bookmarks_pb2.BookmarkStatusResponse(
                    bookmarked=result["bookmarked"],
                )
        except Exception:
            return bookmarks_pb2.BookmarkStatusResponse(bookmarked=False)

    def GetBookmarkedPosts(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            limit = request.limit if request.limit else 20
            offset = request.offset if request.offset else 0

            with SessionLocal() as session:
                posts = get_bookmarked_posts(
                    session,
                    auth["user_id"],
                    auth["user_id"],
                    limit,
                    offset,
                )

                return posts_pb2.PostsResponse(
                    posts=[to_post_response(post) for post in posts],
                )
        except Exception:
            return posts_pb2.PostsResponse(posts=[])
