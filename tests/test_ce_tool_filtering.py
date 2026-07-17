"""Tool-discovery tests for Plane Community Edition mode."""

import asyncio

from plane_mcp.server import get_stdio_mcp
from plane_mcp.tools import CE_UNAVAILABLE_TOOLS


def _tool_names() -> set[str]:
    mcp = get_stdio_mcp()
    return {tool.name for tool in asyncio.run(mcp.list_tools())}


def test_community_mode_hides_unavailable_tools(monkeypatch):
    monkeypatch.setenv("PLANE_MCP_EDITION", "community")

    tool_names = _tool_names()

    assert not tool_names & CE_UNAVAILABLE_TOOLS
    assert "list_projects" in tool_names
    assert "list_work_item_activities" in tool_names
    assert "create_work_item_relation" in tool_names


def test_cloud_mode_keeps_full_tool_surface(monkeypatch):
    monkeypatch.setenv("PLANE_MCP_EDITION", "cloud")

    tool_names = _tool_names()

    assert CE_UNAVAILABLE_TOOLS <= tool_names


def test_auto_mode_detects_a_self_hosted_url(monkeypatch):
    monkeypatch.setenv("PLANE_MCP_EDITION", "auto")
    monkeypatch.delenv("PLANE_INTERNAL_BASE_URL", raising=False)
    monkeypatch.setenv("PLANE_BASE_URL", "https://plane.example.test")

    tool_names = _tool_names()

    assert not tool_names & CE_UNAVAILABLE_TOOLS
