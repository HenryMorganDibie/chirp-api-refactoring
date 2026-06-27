"""Auth service gRPC handler."""

import grpc

from chirp_api.db import SessionLocal
from chirp_api.generated import auth_pb2, auth_pb2_grpc
from chirp_api.middleware.auth import validate_session_token
from chirp_api.services.auth_service import get_current_user, login_user, register_user
from chirp_api.services.utils import to_proto_timestamp


class AuthServiceServicer(auth_pb2_grpc.AuthServiceServicer):
    """Handles authentication RPCs."""

    def Register(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            with SessionLocal() as session:
                result = register_user(
                    session,
                    email=request.email,
                    username=request.username,
                    display_name=request.display_name,
                    password=request.password,
                )

                return auth_pb2.AuthResponse(
                    success=True,
                    user_id=result["user_id"],
                    session_token=result["session_token"],
                )
        except Exception as error:
            return auth_pb2.AuthResponse(
                success=False,
                user_id="",
                session_token="",
                error=str(error),
            )

    def Login(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            with SessionLocal() as session:
                result = login_user(
                    session,
                    email=request.email,
                    password=request.password,
                )

                return auth_pb2.AuthResponse(
                    success=True,
                    user_id=result["user_id"],
                    session_token=result["session_token"],
                )
        except Exception as error:
            return auth_pb2.AuthResponse(
                success=False,
                user_id="",
                session_token="",
                error=str(error),
            )

    def Logout(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        # With JWT, logout is handled client-side by removing the token
        return auth_pb2.LogoutResponse(success=True)

    def GetCurrentUser(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                user = get_current_user(session, auth["user_id"])

                return auth_pb2.UserResponse(
                    id=user["id"],
                    email=user["email"],
                    username=user["username"],
                    display_name=user["display_name"],
                    avatar_url=user.get("avatar_url") or "",
                    bio=user.get("bio") or "",
                    role=user["role"],
                    created_at=to_proto_timestamp(user["created_at"]),
                )
        except Exception as error:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, str(error))

    def ValidateSession(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            return auth_pb2.ValidateSessionResponse(
                valid=True,
                user_id=auth["user_id"],
                username=auth["username"],
                role=auth["role"],
            )
        except Exception:
            return auth_pb2.ValidateSessionResponse(
                valid=False,
                user_id="",
                username="",
                role="",
            )
