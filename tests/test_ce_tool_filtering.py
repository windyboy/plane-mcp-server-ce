"""Tool-discovery tests for Plane Community Edition mode."""

import asyncio

import pytest

from plane_mcp.server import get_stdio_mcp
from plane_mcp.tools import CE_ONLY_TOOLS, CE_SESSION_TOOLS, CE_UNAVAILABLE_TOOLS


@pytest.fixture(autouse=True)
def _clear_session_env(monkeypatch):
    """Default every test to *no* app-session credentials configured."""
    for var in ("PLANE_SESSION_EMAIL", "PLANE_SESSION_PASSWORD", "PLANE_SESSION_COOKIE"):
        monkeypatch.delenv(var, raising=False)


def _tool_names() -> set[str]:
    mcp = get_stdio_mcp()
    return {tool.name for tool in asyncio.run(mcp.list_tools())}


def _tool(name: str):
    mcp = get_stdio_mcp()
    return next(tool for tool in asyncio.run(mcp.list_tools()) if tool.name == name)


def test_community_mode_hides_unavailable_tools(monkeypatch):
    monkeypatch.setenv("PLANE_MCP_EDITION", "community")

    tool_names = _tool_names()

    assert not tool_names & CE_UNAVAILABLE_TOOLS
    assert "list_projects" in tool_names
    assert "list_work_item_activities" in tool_names
    assert "create_work_item_relation" in tool_names


def test_community_mode_hides_session_tools_without_credentials(monkeypatch):
    monkeypatch.setenv("PLANE_MCP_EDITION", "community")

    tool_names = _tool_names()

    assert not tool_names & CE_SESSION_TOOLS


def test_community_mode_exposes_session_tools_with_credentials(monkeypatch):
    monkeypatch.setenv("PLANE_MCP_EDITION", "community")
    monkeypatch.setenv("PLANE_SESSION_EMAIL", "admin@example.test")
    monkeypatch.setenv("PLANE_SESSION_PASSWORD", "secret")

    tool_names = _tool_names()

    assert CE_SESSION_TOOLS <= tool_names
    assert {"update_page", "update_page_content", "archive_page", "unarchive_page", "delete_page"} <= tool_names
    # Truly-unavailable tools stay hidden regardless of session auth.
    assert not tool_names & CE_UNAVAILABLE_TOOLS


def test_cloud_mode_keeps_full_tool_surface(monkeypatch):
    monkeypatch.setenv("PLANE_MCP_EDITION", "cloud")

    tool_names = _tool_names()

    assert CE_UNAVAILABLE_TOOLS <= tool_names
    assert CE_SESSION_TOOLS - CE_ONLY_TOOLS <= tool_names
    assert not tool_names & CE_ONLY_TOOLS


def test_auto_mode_detects_a_self_hosted_url(monkeypatch):
    monkeypatch.setenv("PLANE_MCP_EDITION", "auto")
    monkeypatch.delenv("PLANE_INTERNAL_BASE_URL", raising=False)
    monkeypatch.setenv("PLANE_BASE_URL", "https://plane.example.test")

    tool_names = _tool_names()

    assert not tool_names & CE_UNAVAILABLE_TOOLS


def test_community_mode_does_not_advertise_unsupported_pql(monkeypatch):
    monkeypatch.setenv("PLANE_MCP_EDITION", "community")

    assert "pql" not in _tool("list_work_items").parameters["properties"]


def test_cloud_mode_keeps_pql(monkeypatch):
    monkeypatch.setenv("PLANE_MCP_EDITION", "cloud")

    assert "pql" in _tool("list_work_items").parameters["properties"]
