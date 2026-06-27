"""Notifications service gRPC handler."""

from chirp_api.db import SessionLocal
from chirp_api.generated import common_pb2, notifications_pb2, notifications_pb2_grpc
from chirp_api.middleware.auth import validate_session_token
from chirp_api.services.notifications_service import (
    delete_notification,
    get_unread_count,
    get_user_notifications,
    mark_all_as_read,
    mark_as_read,
)
from chirp_api.services.utils import to_proto_timestamp


def to_notification_proto(notification):
    """Convert a notification dict to a Notification proto."""
    assert notification is not None, "Notification dict must not be None"

    actor = notification.get("actor")
    if actor:
        actor_proto = common_pb2.Author(
            id=actor.get("id") or "",
            username=actor.get("username") or "",
            display_name=actor.get("display_name") or "",
            avatar_url=actor.get("avatar_url") or "",
        )
    else:
        actor_proto = None

    return notifications_pb2.Notification(
        id=notification["id"],
        type=notification["type"],
        read=notification.get("read") or False,
        actor=actor_proto,
        post_id=notification.get("post_id") or "",
        comment_id=notification.get("comment_id") or "",
        post_content=notification.get("post_content") or "",
        comment_content=notification.get("comment_content") or "",
        created_at=to_proto_timestamp(notification["created_at"]),
    )


class NotificationsServiceServicer(notifications_pb2_grpc.NotificationsServiceServicer):
    """Handles notification RPCs."""

    def GetNotifications(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            limit = request.limit if request.limit else 20
            offset = request.offset if request.offset else 0

            with SessionLocal() as session:
                notifications = get_user_notifications(session, auth["user_id"], limit, offset)

                return notifications_pb2.GetNotificationsResponse(
                    notifications=[
                        to_notification_proto(notification) for notification in notifications
                    ],
                )
        except Exception:
            return notifications_pb2.GetNotificationsResponse(notifications=[])

    def GetUnreadCount(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                result = get_unread_count(session, auth["user_id"])

                return notifications_pb2.GetUnreadCountResponse(count=result["count"])
        except Exception:
            return notifications_pb2.GetUnreadCountResponse(count=0)

    def MarkAsRead(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                mark_as_read(session, request.notification_id, auth["user_id"])

                return notifications_pb2.MarkAsReadResponse(success=True)
        except Exception:
            return notifications_pb2.MarkAsReadResponse(success=True)

    def MarkAllAsRead(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                mark_all_as_read(session, auth["user_id"])

                return notifications_pb2.MarkAllAsReadResponse(success=True)
        except Exception:
            return notifications_pb2.MarkAllAsReadResponse(success=True)

    def DeleteNotification(self, request, context):
        assert request is not None, "Request must not be None"
        assert context is not None, "Context must not be None"

        try:
            auth = validate_session_token(request.session_token)

            with SessionLocal() as session:
                delete_notification(session, request.notification_id, auth["user_id"])

                return notifications_pb2.DeleteNotificationResponse(success=True)
        except Exception:
            return notifications_pb2.DeleteNotificationResponse(success=True)
