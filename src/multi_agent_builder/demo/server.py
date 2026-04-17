"""
HTTP server for the Multi-Agent Builder demo UI.

This module runs a simple web server that serves the browser-based interface
for submitting product ideas and monitoring build progress in real-time.
"""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os

from ..orchestration.retry import RetryPolicy
from .app import DemoApplication


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the demo server."""
    parser = argparse.ArgumentParser(description="Serve the Codex Creator Challenge demo UI")
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"), help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")), help="Port to run the server on")
    parser.add_argument("--output-root", default=os.getenv("OUTPUT_ROOT", "runs"), help="Directory for build outputs")
    parser.add_argument("--max-test-retries", type=int, default=2, help="Maximum test retries")
    parser.add_argument("--max-architecture-retries", type=int, default=1, help="Maximum architecture retries")
    return parser


def serve(host: str, port: int, output_root: str, max_test_retries: int, max_architecture_retries: int) -> None:
    """Start the HTTP server with the demo application."""
    # Initialize the demo app with retry policies
    app = DemoApplication(
        output_root=output_root,
        retry_policy=RetryPolicy(
            max_test_retries=max_test_retries,
            max_architecture_retries=max_architecture_retries,
        ),
    )

    class RequestHandler(BaseHTTPRequestHandler):
        """Custom request handler for the demo server."""

        def _send(self, response) -> None:
            """Send an HTTP response."""
            self.send_response(response.status_code)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(response.body)))
            self.end_headers()
            self.wfile.write(response.body)

        def do_GET(self) -> None:  # noqa: N802
            """Handle GET requests."""
            self._send(app.handle("GET", self.path))

        def do_POST(self) -> None:  # noqa: N802
            """Handle POST requests."""
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b""
            self._send(app.handle("POST", self.path, body))

        def log_message(self, format: str, *args: object) -> None:
            """Suppress default logging."""
            return

    # Start the server indefinitely
    ThreadingHTTPServer((host, port), RequestHandler).serve_forever()


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the demo server."""
    args = build_parser().parse_args(argv)
    serve(
        host=args.host,
        port=args.port,
        output_root=args.output_root,
        max_test_retries=args.max_test_retries,
        max_architecture_retries=args.max_architecture_retries,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

