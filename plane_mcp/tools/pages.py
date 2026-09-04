"""Page-related tools for Plane MCP Server."""

from typing import Any

from fastmcp import FastMCP
from plane.models.pages import CreatePage, Page, UpdatePage
from plane.models.work_item_pages import CreateWorkItemPage, WorkItemPage

from plane_mcp.client import get_plane_client_context
from plane_mcp.page_backends import get_page_backend

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

        return get_page_backend(client, workspace_slug).list_pages(project_id, params)

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

        return get_page_backend(client, workspace_slug).retrieve_page(page_id, project_id)

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
        parent_id: str | None = None,
        collection_id: str | None = None,
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
            parent_id: Parent page UUID. Cloud only until a CE target supports it.
            collection_id: Collection UUID. Cloud only until a CE target supports it.

        Returns:
            Created Page object
        """
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
            parent_id=parent_id,
            collection_id=collection_id,
        )

        client, workspace_slug = get_plane_client_context()
        return get_page_backend(client, workspace_slug).create_page(data, project_id)

    @mcp.tool()
    def update_page(
        page_id: str,
        project_id: str,
        name: str | None = None,
        description_html: str | None = None,
    ) -> Page:
        """Update a project page's name and/or HTML content.

        At least one field is required. Cloud performs one SDK update; CE applies
        name and content through its verified app routes, in that order.
        """
        if name is None and description_html is None:
            raise ValueError("Pass name and/or description_html when updating a page.")
        client, workspace_slug = get_plane_client_context()
        return get_page_backend(client, workspace_slug).update_page(
            page_id, project_id, UpdatePage(name=name, description_html=description_html)
        )

    @mcp.tool()
    def update_page_content(
        page_id: str,
        description_html: str,
        project_id: str,
    ) -> Page:
        """Compatibility entry point for updating a page's HTML content."""
        return update_page(page_id, project_id, description_html=description_html)

    @mcp.tool()
    def archive_page(page_id: str, project_id: str) -> Page:
        """Archive a project page through the SDK or CE app-session backend."""
        client, workspace_slug = get_plane_client_context()
        return get_page_backend(client, workspace_slug).archive_page(page_id, project_id)

    @mcp.tool()
    def unarchive_page(page_id: str, project_id: str) -> Page:
        """Unarchive a project page through the SDK or CE app-session backend."""
        client, workspace_slug = get_plane_client_context()
        return get_page_backend(client, workspace_slug).unarchive_page(page_id, project_id)

    @mcp.tool()
    def delete_page(page_id: str, project_id: str) -> None:
        """Delete an archived project-root page through the CE app-session API.

        Plane CE rejects deletion of an active page; call ``archive_page`` and
        read it back before deleting.
        """
        client, workspace_slug = get_plane_client_context()
        get_page_backend(client, workspace_slug).delete_page(page_id, project_id)
