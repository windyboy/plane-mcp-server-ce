"""Page-related tools for Plane MCP Server."""

from typing import Any

from fastmcp import FastMCP
from plane.errors.errors import HttpError
from plane.models.pages import CreatePage, Page
from plane.models.work_item_pages import CreateWorkItemPage, WorkItemPage

from plane_mcp.app_session import get_app_session, route_via_app_session
from plane_mcp.client import get_plane_client_context

# Community Edition serves pages only on the app API, in *project* scope. Workspace
# pages and work-item<->page links do not exist on CE at all (see CE_COMPAT.md).
_CE_WORKSPACE_PAGES = "Workspace-level pages are not available on Plane Community Edition; pass project_id."


def register_page_tools(mcp: FastMCP) -> None:
    """Register all page-related tools with the MCP server."""

    @mcp.tool()
    def list_pages(
        project_id: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> list[Page]:
        """
        List pages.

        Lists a project's pages if project_id is given, otherwise workspace-level pages.

        Args:
            project_id: UUID of the project. Omit to list workspace pages.
            params: Optional query parameters as a dictionary (e.g., per_page, cursor)

        Returns:
            List of Page objects
        """
        client, workspace_slug = get_plane_client_context()

        if route_via_app_session():
            if project_id is None:
                raise ValueError(_CE_WORKSPACE_PAGES)
            data = get_app_session().get(f"workspaces/{workspace_slug}/projects/{project_id}/pages/", params=params)
            return [Page.model_validate(p) for p in (data or [])]

        if project_id is not None:
            response = client.pages.list_project_pages(
                workspace_slug=workspace_slug, project_id=project_id, params=params
            )
        else:
            response = client.pages.list_workspace_pages(workspace_slug=workspace_slug, params=params)
        return response.results

    @mcp.tool()
    def attach_page_to_work_item(
        project_id: str,
        work_item_id: str,
        page_id: str,
    ) -> WorkItemPage:
        """
        Link a page to a work item.

        Args:
            project_id: UUID of the project
            work_item_id: UUID of the work item
            page_id: UUID of the page to link

        Returns:
            WorkItemPage link object
        """
        client, workspace_slug = get_plane_client_context()
        return client.work_items.pages.create(
            workspace_slug=workspace_slug,
            project_id=project_id,
            work_item_id=work_item_id,
            data=CreateWorkItemPage(page_id=page_id),
        )

    @mcp.tool()
    def list_work_item_pages(
        project_id: str,
        work_item_id: str,
    ) -> list[WorkItemPage]:
        """
        List all pages linked to a work item.

        Args:
            project_id: UUID of the project
            work_item_id: UUID of the work item

        Returns:
            List of WorkItemPage link objects
        """
        client, workspace_slug = get_plane_client_context()
        response = client.work_items.pages.list(
            workspace_slug=workspace_slug,
            project_id=project_id,
            work_item_id=work_item_id,
        )
        return response.results

    @mcp.tool()
    def detach_page_from_work_item(
        project_id: str,
        work_item_id: str,
        work_item_page_id: str,
    ) -> None:
        """
        Remove a page link from a work item.

        Args:
            project_id: UUID of the project
            work_item_id: UUID of the work item
            work_item_page_id: UUID of the work item page link (not the page ID)
        """
        client, workspace_slug = get_plane_client_context()
        client.work_items.pages.delete(
            workspace_slug=workspace_slug,
            project_id=project_id,
            work_item_id=work_item_id,
            work_item_page_id=work_item_page_id,
        )

    @mcp.tool()
    def retrieve_page(
        page_id: str,
        project_id: str | None = None,
    ) -> Page:
        """
        Retrieve a page by ID.

        Retrieves a project page if project_id is given, otherwise a workspace page.

        Args:
            page_id: UUID of the page
            project_id: UUID of the project. Omit for a workspace page.

        Returns:
            Page object
        """
        client, workspace_slug = get_plane_client_context()

        if route_via_app_session():
            if project_id is None:
                raise ValueError(_CE_WORKSPACE_PAGES)
            data = get_app_session().get(f"workspaces/{workspace_slug}/projects/{project_id}/pages/{page_id}/")
            return Page.model_validate(data)

        if project_id is not None:
            return client.pages.retrieve_project_page(
                workspace_slug=workspace_slug,
                project_id=project_id,
                page_id=page_id,
            )
        return client.pages.retrieve_workspace_page(
            workspace_slug=workspace_slug,
            page_id=page_id,
        )

    @mcp.tool()
    def create_page(
        name: str,
        description_html: str,
        project_id: str | None = None,
        access: int | None = None,
        color: str | None = None,
        is_locked: bool | None = None,
        archived_at: str | None = None,
        view_props: dict[str, Any] | None = None,
        logo_props: dict[str, Any] | None = None,
        external_id: str | None = None,
        external_source: str | None = None,
    ) -> Page:
        """
        Create a page.

        Creates a project page if project_id is given, otherwise a
        workspace-level page.

        Args:
            name: Page name
            description_html: Page content in HTML format
            project_id: UUID of the project. Omit to create a workspace page.
            access: Access level for the page (integer)
            color: Page color
            is_locked: Whether the page is locked
            archived_at: Archive timestamp (ISO 8601 format)
            view_props: View properties dictionary
            logo_props: Logo properties dictionary
            external_id: External system identifier
            external_source: External system source name

        Returns:
            Created Page object
        """
        client, workspace_slug = get_plane_client_context()

        if route_via_app_session():
            if project_id is None:
                raise ValueError(_CE_WORKSPACE_PAGES)
            # The CE app page-create endpoint takes name + simple metadata;
            # collaborative content is applied on its separate endpoint below.
            body: dict[str, Any] = {"name": name}
            for key, value in {
                "access": access,
                "color": color,
                "is_locked": is_locked,
                "view_props": view_props,
                "logo_props": logo_props,
            }.items():
                if value is not None:
                    body[key] = value
            app = get_app_session()
            base = f"workspaces/{workspace_slug}/projects/{project_id}/pages/"
            created = app.post(base, json=body)
            page_id = created["id"]
            if description_html:
                # CE stores collaborative content on a separate, proven route.
                # Do this explicitly so the tool never claims content was saved
                # when the create endpoint accepted only the page metadata.
                try:
                    app.patch(f"{base}{page_id}/description/", json={"description_html": description_html})
                except HttpError as exc:
                    raise HttpError(
                        f"Page {page_id} was created but its content update failed; use update_page_content to retry.",
                        exc.status_code,
                        exc.response,
                    ) from exc
            return Page.model_validate(app.get(f"{base}{page_id}/"))

        data = CreatePage(
            name=name,
            description_html=description_html,
            access=access,
            color=color,
            is_locked=is_locked,
            archived_at=archived_at,
            view_props=view_props,
            logo_props=logo_props,
            external_id=external_id,
            external_source=external_source,
        )

        if project_id is not None:
            return client.pages.create_project_page(
                workspace_slug=workspace_slug,
                project_id=project_id,
                data=data,
            )
        return client.pages.create_workspace_page(
            workspace_slug=workspace_slug,
            data=data,
        )

    @mcp.tool()
    def update_page(
        page_id: str,
        name: str,
        project_id: str,
    ) -> Page:
        """Rename a project-root page through the CE app-session API.

        This operation is exposed in CE only when session credentials are
        configured. Cloud update support awaits a public SDK method.
        """
        if not route_via_app_session():
            raise NotImplementedError("update_page currently requires Plane CE app-session credentials.")
        _, workspace_slug = get_plane_client_context()
        path = f"workspaces/{workspace_slug}/projects/{project_id}/pages/{page_id}/"
        get_app_session().patch(path, json={"name": name})
        return Page.model_validate(get_app_session().get(path))

    @mcp.tool()
    def update_page_content(
        page_id: str,
        description_html: str,
        project_id: str,
    ) -> Page:
        """Update a project-root page's HTML content through the CE app API."""
        if not route_via_app_session():
            raise NotImplementedError("update_page_content currently requires Plane CE app-session credentials.")
        _, workspace_slug = get_plane_client_context()
        base = f"workspaces/{workspace_slug}/projects/{project_id}/pages/{page_id}/"
        get_app_session().patch(f"{base}description/", json={"description_html": description_html})
        return Page.model_validate(get_app_session().get(base))

    @mcp.tool()
    def archive_page(page_id: str, project_id: str) -> Page:
        """Archive a project-root page through the CE app-session API."""
        if not route_via_app_session():
            raise NotImplementedError("archive_page currently requires Plane CE app-session credentials.")
        _, workspace_slug = get_plane_client_context()
        base = f"workspaces/{workspace_slug}/projects/{project_id}/pages/{page_id}/"
        get_app_session().post(f"{base}archive/", json={})
        return Page.model_validate(get_app_session().get(base))

    @mcp.tool()
    def unarchive_page(page_id: str, project_id: str) -> Page:
        """Unarchive a project-root page through the CE app-session API."""
        if not route_via_app_session():
            raise NotImplementedError("unarchive_page currently requires Plane CE app-session credentials.")
        _, workspace_slug = get_plane_client_context()
        base = f"workspaces/{workspace_slug}/projects/{project_id}/pages/{page_id}/"
        get_app_session().delete(f"{base}archive/")
        return Page.model_validate(get_app_session().get(base))

    @mcp.tool()
    def delete_page(page_id: str, project_id: str) -> None:
        """Delete an archived project-root page through the CE app-session API.

        Plane CE rejects deletion of an active page; call ``archive_page`` and
        read it back before deleting.
        """
        client, workspace_slug = get_plane_client_context()
        if route_via_app_session():
            get_app_session().delete(f"workspaces/{workspace_slug}/projects/{project_id}/pages/{page_id}/")
            return
        client.pages.delete_project_page(workspace_slug=workspace_slug, project_id=project_id, page_id=page_id)
