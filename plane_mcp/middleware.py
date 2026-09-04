"""Custom FastMCP middleware for the Plane MCP Server."""

from __future__ import annotations

import logging
import time
from typing import Any

from fastmcp.server.middleware import MiddlewareContext
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware


class PlaneLoggingMiddleware(StructuredLoggingMiddleware):
    """Emit one structured event for each tool invocation.

    Protocol traffic such as initialize, ping, and tools/list is intentionally
    excluded. Tool arguments can be enabled explicitly for short-lived
    debugging, but are not safe or useful enough to log by default.
    """

    def __init__(self, *, include_payloads: bool = False) -> None:
        super().__init__(
            include_payloads=include_payloads,
            methods=["tools/call"],
        )

    def _with_tool_name(self, context: MiddlewareContext[Any], message: dict) -> dict:
        params = getattr(context.message, "params", context.message)
        message["tool"] = getattr(params, "name", "unknown")
        return message

    def _create_after_message(self, context: MiddlewareContext[Any], start_time: float) -> dict:
        message = super()._create_after_message(context, start_time)
        message["event"] = "tool_success"
        return self._with_tool_name(context, message)

    def _create_error_message(
        self, context: MiddlewareContext[Any], start_time: float, error: Exception
    ) -> dict:
        message = super()._create_error_message(context, start_time, error)
        message["event"] = "tool_error"
        return self._with_tool_name(context, message)

    async def on_message(self, context: MiddlewareContext[Any], call_next: Any) -> Any:
        """Log completion or failure, rather than both start and completion."""
        if context.method != "tools/call":
            return await call_next(context)

        start_time = time.perf_counter()
        try:
            result = await call_next(context)
        except Exception as error:
            self._log_message(self._create_error_message(context, start_time, error), logging.ERROR)
            raise

        self._log_message(self._create_after_message(context, start_time))
        return result
