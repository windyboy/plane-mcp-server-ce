"""FastMCP server factories for the supported transports."""

from __future__ import annotations

from fastmcp import FastMCP

from plane_mcp.auth import PlaneHeaderAuthProvider
from plane_mcp.instructions import SERVER_INSTRUCTIONS
from plane_mcp.middleware import PlaneLoggingMiddleware
from plane_mcp.tools import register_tools


def get_header_mcp():
    header_mcp = FastMCP(
        "Plane MCP Server (header-http)",
        instructions=SERVER_INSTRUCTIONS,
        auth=PlaneHeaderAuthProvider(
            required_scopes=["read", "write"],
        ),
    )
    header_mcp.add_middleware(PlaneLoggingMiddleware())
    register_tools(header_mcp)
    return header_mcp


def get_stdio_mcp():
    stdio_mcp = FastMCP(
        "Plane MCP Server (stdio)",
        instructions=SERVER_INSTRUCTIONS,
    )
    stdio_mcp.add_middleware(PlaneLoggingMiddleware())
    register_tools(stdio_mcp)
    return stdio_mcp
