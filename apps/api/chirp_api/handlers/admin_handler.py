"""Admin service gRPC handler.

All methods require admin authentication. Uses require_admin check,
then returns error responses on failure.
"""

from chirp_api.db import SessionLocal
from chirp_api.generated import admin_pb2, admin_pb2_grpc
from chirp_api.middleware.auth import require_admin, validate_session_token
from chirp_api.services.admin_service import (
    ban_user,
    delete_comment_admin,
    delete_post_admin,
    delete_user,
    get_audit_logs,
    get_dashboard_stats,
    get_report,
    get_user_details,
    list_reports,
    list_users,
    review_report,
    unban_user,
    update_user_role,
)
from chirp_api.services.utils import to_proto_timestamp


def to_admin_user_response(user):
    """Convert an admin user dict to an AdminUserResponse proto."""
    assert user is not None, "User dict must not be None"

    banned_at = None
    if user.get("banned_at"):
        banned_at = to_proto_timestamp(user["banned_at"])

    return admin_pb2.AdminUserResponse(
        id=user["id"],
        email=user["email"],
        username=user["username"],
        display_name=user["display_name"],
        avatar_url=user.get("avatar_url") or "",
        bio=user.get("bio") or "",
        role=user["role"],
        created_at=to_proto_timestamp(user["created_at"]),
        updated_at=to_proto_timestamp(user["updated_at"]),
        banned_at=banned_at,
        banned_reason=user.get("banned_reason") or "",
        post_count=user.get("post_count") or 0,
        comment_count=user.get("comment_count") or 0,
    )


def to_report_response(report):
    """Convert a report dict to a ReportResponse proto."""
    assert report is not None, "Report dict must not be None"

    reviewed_at = None
    if report.get("reviewed_at"):
        reviewed_at = to_proto_timestamp(report["reviewed_at"])

    return admin_pb2.ReportResponse(
        id=report["id"],
        reporter_id=report["reporter_id"],
        reporter_username=report["reporter_username"],
        target_type=report["target_type"],
        target_id=report["target_id"],
        reason=report["reason"],
        description=report.get("description") or "",
        status=report["status"],
        reviewed_by=report.get("reviewed_by") or "",
        reviewed_at=reviewed_at,
        created_at=to_proto_timestamp(report["created_at"]),
    )


def to_audit_log_response(log):
    """Convert an audit log dict to an AuditLogResponse proto."""
    assert log is not None, "Audit log dict must not be None"

    return admin_pb2.AuditLogResponse(
        id=log["id"],
        admin_id=log["admin_id"],
        admin_username=log["admin_username"],
        action=log["action"],
        target_type=log.get("target_type") or "",
        target_id=log.get("target_id") or "",
        details=log.get("details") or "",
        ip_address=log.get("ip_address") or "",
        created_at=to_proto_timestamp(log["created_at"]),
    )


class AdminServiceServicer(admin_pb2_grpc.AdminServiceServicer):
    """Handles admin RPCs. All methods require admin authentication."""

    def ListUsers(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        auth = validate_session_token(request.session_token)
        require_admin(auth)

        pagination = request.pagination
        limit = pagination.limit if pagination and pagination.limit else 20
        offset = pagination.offset if pagination and pagination.offset else 0

        with SessionLocal() as session:
            result = list_users(
                session,
                limit=limit,
                offset=offset,
                search_query=request.search_query or None,
                role_filter=request.role_filter or None,
            )

            return admin_pb2.ListUsersResponse(
                users=[to_admin_user_response(user) for user in result["users"]],
                total=result["total"],
            )

    def GetUserDetails(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        auth = validate_session_token(request.session_token)
        require_admin(auth)

        with SessionLocal() as session:
            user = get_user_details(session, request.user_id)

            return admin_pb2.UserDetailsResponse(
                user=to_admin_user_response(user),
            )

    def BanUser(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)
            require_admin(auth)

            with SessionLocal() as session:
                ban_user(session, request.user_id, request.reason, auth["user_id"])

                return admin_pb2.BanUserResponse(success=True)
        except Exception as error:
            return admin_pb2.BanUserResponse(
                success=False,
                error=str(error),
            )

    def UnbanUser(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)
            require_admin(auth)

            with SessionLocal() as session:
                unban_user(session, request.user_id, auth["user_id"])

                return admin_pb2.UnbanUserResponse(success=True)
        except Exception as error:
            return admin_pb2.UnbanUserResponse(
                success=False,
                error=str(error),
            )

    def UpdateUserRole(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)
            require_admin(auth)

            with SessionLocal() as session:
                update_user_role(session, request.user_id, request.role, auth["user_id"])

                return admin_pb2.UpdateUserRoleResponse(success=True)
        except Exception as error:
            return admin_pb2.UpdateUserRoleResponse(
                success=False,
                error=str(error),
            )

    def DeleteUser(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)
            require_admin(auth)

            with SessionLocal() as session:
                delete_user(session, request.user_id, auth["user_id"])

                return admin_pb2.DeleteUserResponse(success=True)
        except Exception as error:
            return admin_pb2.DeleteUserResponse(
                success=False,
                error=str(error),
            )

    def DeletePostAdmin(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)
            require_admin(auth)

            with SessionLocal() as session:
                delete_post_admin(session, request.post_id, request.reason, auth["user_id"])

                return admin_pb2.DeletePostAdminResponse(success=True)
        except Exception as error:
            return admin_pb2.DeletePostAdminResponse(
                success=False,
                error=str(error),
            )

    def DeleteCommentAdmin(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)
            require_admin(auth)

            with SessionLocal() as session:
                delete_comment_admin(session, request.comment_id, request.reason, auth["user_id"])

                return admin_pb2.DeleteCommentAdminResponse(success=True)
        except Exception as error:
            return admin_pb2.DeleteCommentAdminResponse(
                success=False,
                error=str(error),
            )

    def ListReports(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        auth = validate_session_token(request.session_token)
        require_admin(auth)

        pagination = request.pagination
        limit = pagination.limit if pagination and pagination.limit else 20
        offset = pagination.offset if pagination and pagination.offset else 0

        with SessionLocal() as session:
            result = list_reports(
                session,
                limit=limit,
                offset=offset,
                status_filter=request.status_filter or None,
                type_filter=request.type_filter or None,
            )

            return admin_pb2.ListReportsResponse(
                reports=[to_report_response(report) for report in result["reports"]],
                total=result["total"],
            )

    def GetReport(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        auth = validate_session_token(request.session_token)
        require_admin(auth)

        with SessionLocal() as session:
            report = get_report(session, request.report_id)

            return to_report_response(report)

    def ReviewReport(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)
            require_admin(auth)

            with SessionLocal() as session:
                review_report(
                    session,
                    request.report_id,
                    request.action,
                    auth["user_id"],
                    request.notes or None,
                )

                return admin_pb2.ReviewReportResponse(success=True)
        except Exception as error:
            return admin_pb2.ReviewReportResponse(
                success=False,
                error=str(error),
            )

    def GetDashboardStats(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        auth = validate_session_token(request.session_token)
        require_admin(auth)

        with SessionLocal() as session:
            stats = get_dashboard_stats(session)

            return admin_pb2.DashboardStatsResponse(
                total_users=stats["total_users"],
                total_posts=stats["total_posts"],
                total_comments=stats["total_comments"],
                pending_reports=stats["pending_reports"],
                new_users_today=stats["new_users_today"],
                new_posts_today=stats["new_posts_today"],
                banned_users=stats["banned_users"],
            )

    def GetAuditLogs(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        auth = validate_session_token(request.session_token)
        require_admin(auth)

        pagination = request.pagination
        limit = pagination.limit if pagination and pagination.limit else 50
        offset = pagination.offset if pagination and pagination.offset else 0

        with SessionLocal() as session:
            result = get_audit_logs(
                session,
                limit=limit,
                offset=offset,
                admin_id_filter=request.admin_id_filter or None,
                action_filter=request.action_filter or None,
            )

            return admin_pb2.AuditLogsResponse(
                logs=[to_audit_log_response(log) for log in result["logs"]],
                total=result["total"],
            )
