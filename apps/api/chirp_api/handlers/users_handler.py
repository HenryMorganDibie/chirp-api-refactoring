"""Users service gRPC handler.

Optional auth pattern: tries to validate token, ignores errors.
"""

from chirp_api.db import SessionLocal
from chirp_api.generated import users_pb2, users_pb2_grpc
from chirp_api.middleware.auth import validate_session_token
from chirp_api.services.users_service import get_user, update_profile
from chirp_api.services.utils import to_proto_timestamp


class UsersServiceServicer(users_pb2_grpc.UsersServiceServicer):
    """Handles user profile RPCs."""

    def GetUser(self, request, context):
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
                user = get_user(session, request.username, user_id)

                return users_pb2.UserProfileResponse(
                    id=user["id"],
                    email=user["email"],
                    username=user["username"],
                    display_name=user["display_name"],
                    avatar_url=user.get("avatar_url") or "",
                    bio=user.get("bio") or "",
                    role=user["role"],
                    created_at=to_proto_timestamp(user["created_at"]),
                    follower_count=user.get("follower_count") or 0,
                    following_count=user.get("following_count") or 0,
                    post_count=user.get("post_count") or 0,
                    is_following=user.get("is_following") or False,
                )
        except Exception:
            return users_pb2.UserProfileResponse(
                id="",
                email="",
                username="",
                display_name="",
                role="",
            )

    def UpdateProfile(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                update_profile(
                    session,
                    user_id=auth["user_id"],
                    display_name=request.display_name or None,
                    bio=request.bio or None,
                    avatar_url=request.avatar_url or None,
                )

                return users_pb2.UpdateProfileResponse(success=True)
        except Exception as error:
            return users_pb2.UpdateProfileResponse(
                success=False,
                error=str(error),
            )
