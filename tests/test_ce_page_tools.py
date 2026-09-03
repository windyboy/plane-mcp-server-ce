"""Unit tests for CE Pages mutations; no live Plane instance required."""

import asyncio

from fastmcp import FastMCP
from plane.errors.errors import HttpError

from plane_mcp.tools import pages


class _AppSession:
    def __init__(self):
        self.calls = []

    def get(self, path, **kwargs):
        self.calls.append(("get", path, kwargs))
        return {"id": "page-1", "name": "saved", "description_html": "<p>saved</p>"}

    def post(self, path, **kwargs):
        self.calls.append(("post", path, kwargs))
        if path.endswith("pages/"):
            return {"id": "page-1"}
        return {"archived_at": "2026-09-03T00:00:00Z"}

    def patch(self, path, **kwargs):
        self.calls.append(("patch", path, kwargs))
        if path.endswith("description/"):
            return {"message": "updated"}
        return {"id": "page-1", "name": "renamed"}

    def delete(self, path, **kwargs):
        self.calls.append(("delete", path, kwargs))


def _tools(monkeypatch):
    app = _AppSession()
    monkeypatch.setattr(pages, "route_via_app_session", lambda: True)
    monkeypatch.setattr(pages, "get_app_session", lambda: app)
    monkeypatch.setattr(pages, "get_plane_client_context", lambda: (object(), "space"))
    mcp = FastMCP("test")
    pages.register_page_tools(mcp)
    tools = {tool.name: tool.fn for tool in asyncio.run(mcp.list_tools())}
    return app, tools


def test_create_page_persists_ce_content(monkeypatch):
    app, tools = _tools(monkeypatch)

    page = tools["create_page"]("title", "<p>body</p>", project_id="project-1")

    assert page.id == "page-1"
    assert app.calls == [
        ("post", "workspaces/space/projects/project-1/pages/", {"json": {"name": "title"}}),
        (
            "patch",
            "workspaces/space/projects/project-1/pages/page-1/description/",
            {"json": {"description_html": "<p>body</p>"}},
        ),
        ("get", "workspaces/space/projects/project-1/pages/page-1/", {}),
    ]


def test_create_page_reports_page_id_when_content_update_fails(monkeypatch):
    app, tools = _tools(monkeypatch)
    app.patch = lambda *args, **kwargs: (_ for _ in ()).throw(HttpError("bad HTML", 422, {}))

    try:
        tools["create_page"]("title", "<p>body</p>", project_id="project-1")
    except HttpError as exc:
        assert "page-1" in str(exc)
    else:
        raise AssertionError("expected content update failure")


def test_ce_page_mutations_use_proven_routes(monkeypatch):
    app, tools = _tools(monkeypatch)

    tools["update_page"]("page-1", "renamed", "project-1")
    tools["update_page_content"]("page-1", "<p>new</p>", "project-1")
    tools["archive_page"]("page-1", "project-1")
    tools["unarchive_page"]("page-1", "project-1")
    tools["delete_page"]("page-1", "project-1")

    assert app.calls == [
        ("patch", "workspaces/space/projects/project-1/pages/page-1/", {"json": {"name": "renamed"}}),
        ("get", "workspaces/space/projects/project-1/pages/page-1/", {}),
        (
            "patch",
            "workspaces/space/projects/project-1/pages/page-1/description/",
            {"json": {"description_html": "<p>new</p>"}},
        ),
        ("get", "workspaces/space/projects/project-1/pages/page-1/", {}),
        ("post", "workspaces/space/projects/project-1/pages/page-1/archive/", {"json": {}}),
        ("get", "workspaces/space/projects/project-1/pages/page-1/", {}),
        ("delete", "workspaces/space/projects/project-1/pages/page-1/archive/", {}),
        ("get", "workspaces/space/projects/project-1/pages/page-1/", {}),
        ("delete", "workspaces/space/projects/project-1/pages/page-1/", {}),
    ]
