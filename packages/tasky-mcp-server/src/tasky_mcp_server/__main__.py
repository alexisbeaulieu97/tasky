"""MCP server entrypoint for standalone execution."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from tasky_mcp_server.config import MCPServerSettings
from tasky_mcp_server.server import MCPServer

logger = logging.getLogger(__name__)


def setup_logging(*, debug: bool = False) -> None:
    """Configure logging for the MCP server."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def main() -> None:
    """Start and run the MCP server."""
    parser = argparse.ArgumentParser(description="Tasky MCP Server")
    parser.add_argument(
        "--project-path",
        type=Path,
        help="Path to the project (default: current directory)",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Host to bind (reserved for future transports)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind (reserved for future transports)",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=None,
        help="Override request timeout in seconds",
    )
    parser.add_argument(
        "--max-concurrent-requests",
        type=int,
        default=None,
        help="Maximum concurrent MCP requests",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    setup_logging(debug=args.debug)

    settings_kwargs: dict[str, object] = {
        "project_path": args.project_path or Path.cwd(),
    }
    if args.host:
        settings_kwargs["host"] = str(args.host)
    if args.port:
        settings_kwargs["port"] = int(args.port)
    if args.timeout_seconds:
        settings_kwargs["timeout_seconds"] = int(args.timeout_seconds)
    if args.max_concurrent_requests:
        settings_kwargs["max_concurrent_requests"] = int(args.max_concurrent_requests)

    settings = MCPServerSettings(**settings_kwargs)  # type: ignore[arg-type]

    server = MCPServer(settings)
    logger.info(
        "Tasky MCP server starting (transport=stdio host=%s port=%s project=%s)",
        settings.host,
        settings.port,
        settings.project_path,
    )
    await server.serve_stdio()
    logger.info("Tasky MCP server stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
