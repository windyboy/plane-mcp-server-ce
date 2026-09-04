"""Page backends for Plane Cloud and Community Edition.

The public SDK and CE's session-authenticated app API expose different page
routes.  Keep that difference below the MCP tool layer while retaining the SDK
``Page`` model as the one return type.
"""

from __future__ import annotations

from typing import Any, Protocol

from plane import PlaneClient
from plane.errors.errors import HttpError
from plane.models.pages import CreatePage, Page, UpdatePage

from plane_mcp.app_session import get_app_session, route_via_app_session


class PageBackend(Protocol):
    """Thin page-operation boundary; implementations return SDK models."""

    def list_pages(self, project_id: str | None, params: dict[str, Any] | None) -> list[Page]: ...

    def retrieve_page(self, page_id: str, project_id: str | None) -> Page: ...

    def create_page(self, data: CreatePage, project_id: str | None) -> Page: ...

    def update_page(self, page_id: str, project_id: str, data: UpdatePage) -> Page: ...

    def archive_page(self, page_id: str, project_id: str) -> Page: ...

    def unarchive_page(self, page_id: str, project_id: str) -> Page: ...

    def delete_page(self, page_id: str, project_id: str) -> None: ...


class CloudPageBackend:
    """Public ``/api/v1`` page operations supplied by ``plane-sdk``."""

    def __init__(self, client: PlaneClient, workspace_slug: str):
        self.client = client
        self.workspace_slug = workspace_slug

    def list_pages(self, project_id: str | None, params: dict[str, Any] | None) -> list[Page]:
        if project_id is None:
            return self.client.pages.list_workspace_pages(self.workspace_slug, params=params).results
        return self.client.pages.list_project_pages(self.workspace_slug, project_id, params=params).results

    def retrieve_page(self, page_id: str, project_id: str | None) -> Page:
        if project_id is None:
            return self.client.pages.retrieve_workspace_page(self.workspace_slug, page_id)
        return self.client.pages.retrieve_project_page(self.workspace_slug, project_id, page_id)

    def create_page(self, data: CreatePage, project_id: str | None) -> Page:
        if project_id is None:
            return self.client.pages.create_workspace_page(self.workspace_slug, data)
        return self.client.pages.create_project_page(self.workspace_slug, project_id, data)

    def update_page(self, page_id: str, project_id: str, data: UpdatePage) -> Page:
        return self.client.pages.update_project_page(self.workspace_slug, project_id, page_id, data)

    def archive_page(self, page_id: str, project_id: str) -> Page:
        self.client.pages.archive_project_page(self.workspace_slug, project_id, page_id)
        return self.retrieve_page(page_id, project_id)

    def unarchive_page(self, page_id: str, project_id: str) -> Page:
        self.client.pages.unarchive_project_page(self.workspace_slug, project_id, page_id)
        return self.retrieve_page(page_id, project_id)

    def delete_page(self, page_id: str, project_id: str) -> None:
        self.client.pages.delete_project_page(self.workspace_slug, project_id, page_id)


class CEPageBackend:
    """Verified project-page operations on CE's session app API."""

    def __init__(self, workspace_slug: str):
        self.workspace_slug = workspace_slug

    def _base(self, project_id: str) -> str:
        return f"workspaces/{self.workspace_slug}/projects/{project_id}/pages/"

    @staticmethod
    def _project_only(project_id: str | None) -> str:
        if project_id is None:
            raise ValueError("Workspace-level pages are not available on Plane Community Edition; pass project_id.")
        return project_id

    def list_pages(self, project_id: str | None, params: dict[str, Any] | None) -> list[Page]:
        project_id = self._project_only(project_id)
        data = get_app_session().get(self._base(project_id), params=params)
        return [Page.model_validate(page) for page in (data or [])]

    def retrieve_page(self, page_id: str, project_id: str | None) -> Page:
        project_id = self._project_only(project_id)
        return Page.model_validate(get_app_session().get(f"{self._base(project_id)}{page_id}/"))

    def create_page(self, data: CreatePage, project_id: str | None) -> Page:
        project_id = self._project_only(project_id)
        # CE has a separate content route; only metadata verified by the probe is
        # sent on create. The v1.4.1 probe showed both hierarchy fields are
        # silently ignored, so reject them before any write.
        if data.parent_id is not None:
            raise ValueError("Nested pages are not available on this Plane Community Edition target.")
        if data.collection_id is not None:
            raise ValueError("Page collections are not available on this Plane Community Edition target.")
        body = {key: value for key, value in {
            "access": data.access,
            "color": data.color,
            "is_locked": data.is_locked,
            "view_props": data.view_props,
            "logo_props": data.logo_props,
        }.items() if value is not None}
        body["name"] = data.name
        base = self._base(project_id)
        created = get_app_session().post(base, json=body)
        page_id = created["id"]
        if data.description_html:
            try:
                get_app_session().patch(
                    f"{base}{page_id}/description/", json={"description_html": data.description_html}
                )
            except HttpError as exc:
                raise HttpError(
                    f"Page {page_id} was created but its content update failed; use update_page to retry.",
                    exc.status_code,
                    exc.response,
                ) from exc
        return self.retrieve_page(page_id, project_id)

    def update_page(self, page_id: str, project_id: str, data: UpdatePage) -> Page:
        base = self._base(project_id)
        app = get_app_session()
        if data.name is not None:
            app.patch(f"{base}{page_id}/", json={"name": data.name})
        if data.description_html is not None:
            try:
                app.patch(f"{base}{page_id}/description/", json={"description_html": data.description_html})
            except HttpError as exc:
                completed = "name" if data.name is not None else "no fields"
                raise HttpError(
                    f"Page {page_id} was only partially updated ({completed}); retry the description_html update.",
                    exc.status_code,
                    exc.response,
                ) from exc
        return self.retrieve_page(page_id, project_id)

    def archive_page(self, page_id: str, project_id: str) -> Page:
        base = self._base(project_id)
        get_app_session().post(f"{base}{page_id}/archive/", json={})
        return self.retrieve_page(page_id, project_id)

    def unarchive_page(self, page_id: str, project_id: str) -> Page:
        base = self._base(project_id)
        get_app_session().delete(f"{base}{page_id}/archive/")
        return self.retrieve_page(page_id, project_id)

    def delete_page(self, page_id: str, project_id: str) -> None:
        get_app_session().delete(f"{self._base(project_id)}{page_id}/")


def get_page_backend(client: PlaneClient, workspace_slug: str) -> PageBackend:
    """Resolve the backend for this call; do not cache request-specific state."""
    if route_via_app_session():
        return CEPageBackend(workspace_slug)
    return CloudPageBackend(client, workspace_slug)
