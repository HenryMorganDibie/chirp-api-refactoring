"""Chirp API entry point.

Starts a gRPC async server on port 50051 (configurable via GRPC_PORT)
and an HTTP health check server on port 3001 (configurable via HTTP_PORT).

Graceful shutdown on SIGTERM/SIGINT.
"""

import asyncio
import json
import os
import signal
import threading
from concurrent import futures
from http.server import BaseHTTPRequestHandler, HTTPServer

from grpc import aio as grpc_aio

from chirp_api.generated import (
    admin_pb2_grpc,
    auth_pb2_grpc,
    bookmarks_pb2_grpc,
    comments_pb2_grpc,
    feed_pb2_grpc,
    follows_pb2_grpc,
    likes_pb2_grpc,
    notifications_pb2_grpc,
    posts_pb2_grpc,
    search_pb2_grpc,
    users_pb2_grpc,
)
from chirp_api.handlers.admin_handler import AdminServiceServicer
from chirp_api.handlers.auth_handler import AuthServiceServicer
from chirp_api.handlers.bookmarks_handler import BookmarksServiceServicer
from chirp_api.handlers.comments_handler import CommentsServiceServicer
from chirp_api.handlers.feed_handler import FeedServiceServicer
from chirp_api.handlers.follows_handler import FollowsServiceServicer
from chirp_api.handlers.likes_handler import LikesServiceServicer
from chirp_api.handlers.notifications_handler import NotificationsServiceServicer
from chirp_api.handlers.posts_handler import PostsServiceServicer
from chirp_api.handlers.search_handler import SearchServiceServicer
from chirp_api.handlers.users_handler import UsersServiceServicer

# Server configuration with bounded defaults
GRPC_PORT = int(os.environ.get("GRPC_PORT", "50051"))
HTTP_PORT = int(os.environ.get("HTTP_PORT", "3001"))

# Thread pool size for gRPC server
GRPC_THREAD_POOL_SIZE = int(os.environ.get("GRPC_THREAD_POOL_SIZE", "10"))

# Shutdown grace period
SHUTDOWN_GRACE_PERIOD_SECONDS = 5

assert 1 <= GRPC_PORT <= 65535, f"GRPC_PORT must be in range [1, 65535], got {GRPC_PORT}"
assert 1 <= HTTP_PORT <= 65535, f"HTTP_PORT must be in range [1, 65535], got {HTTP_PORT}"
assert GRPC_PORT != HTTP_PORT, f"GRPC_PORT and HTTP_PORT must differ, both are {GRPC_PORT}"
assert (
    1 <= GRPC_THREAD_POOL_SIZE <= 100
), f"GRPC_THREAD_POOL_SIZE must be in range [1, 100], got {GRPC_THREAD_POOL_SIZE}"


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check and service info endpoints."""

    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({"status": "ok", "grpc": f"localhost:{GRPC_PORT}"})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))
        elif self.path == "/":
            body = json.dumps(
                {
                    "name": "Chirp API",
                    "version": "1.0.0",
                    "grpcPort": GRPC_PORT,
                    "httpPort": HTTP_PORT,
                }
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            body = json.dumps({"error": "Not Found"})
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args):
        """Suppress default request logging to avoid noise."""
        pass


def start_health_server(port):
    """Start the HTTP health check server in a daemon thread.

    Returns the HTTPServer instance for shutdown coordination.
    """
    assert 1 <= port <= 65535, f"Health server port must be in range [1, 65535], got {port}"

    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    return server


async def serve():
    """Start the gRPC server and HTTP health check, then wait for shutdown."""

    # Initialize the gRPC async server with bounded thread pool
    grpc_aio.init_grpc_aio()
    server = grpc_aio.server(
        futures.ThreadPoolExecutor(max_workers=GRPC_THREAD_POOL_SIZE),
    )

    # Register all 11 service handlers
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServiceServicer(), server)
    posts_pb2_grpc.add_PostsServiceServicer_to_server(PostsServiceServicer(), server)
    comments_pb2_grpc.add_CommentsServiceServicer_to_server(CommentsServiceServicer(), server)
    likes_pb2_grpc.add_LikesServiceServicer_to_server(LikesServiceServicer(), server)
    follows_pb2_grpc.add_FollowsServiceServicer_to_server(FollowsServiceServicer(), server)
    feed_pb2_grpc.add_FeedServiceServicer_to_server(FeedServiceServicer(), server)
    search_pb2_grpc.add_SearchServiceServicer_to_server(SearchServiceServicer(), server)
    users_pb2_grpc.add_UsersServiceServicer_to_server(UsersServiceServicer(), server)
    admin_pb2_grpc.add_AdminServiceServicer_to_server(AdminServiceServicer(), server)
    notifications_pb2_grpc.add_NotificationsServiceServicer_to_server(
        NotificationsServiceServicer(), server
    )
    bookmarks_pb2_grpc.add_BookmarksServiceServicer_to_server(BookmarksServiceServicer(), server)

    # Bind the gRPC server
    listen_address = f"0.0.0.0:{GRPC_PORT}"
    server.add_insecure_port(listen_address)
    await server.start()

    print(f"   gRPC server bound to port {GRPC_PORT}")

    # Start HTTP health check server (only after gRPC is bound)
    health_server = start_health_server(HTTP_PORT)

    print("Chirp API started")
    print(f"   HTTP server: http://localhost:{HTTP_PORT}")
    print(f"   gRPC server: localhost:{GRPC_PORT}")

    # Set up graceful shutdown
    shutdown_event = asyncio.Event()

    def signal_handler():
        print("Shutting down...")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    # Wait for shutdown signal
    await shutdown_event.wait()

    # Graceful shutdown sequence
    health_server.shutdown()
    await server.stop(grace=SHUTDOWN_GRACE_PERIOD_SECONDS)

    print("Chirp API stopped")


def main():
    """Entry point for the Chirp API server."""
    asyncio.run(serve())


if __name__ == "__main__":
    main()
