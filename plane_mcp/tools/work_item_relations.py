"""Work item relation tools for Plane MCP Server.

Plane Community Edition exposes its relation API at ``work-items/{id}/relations``.
It supports the eight built-in relation types directly; the older Cloud endpoints
for dependencies and custom relation definitions are not present on CE.
"""

from typing import Any, get_args

from fastmcp import FastMCP
from plane.models.work_items import (
    CreateWorkItemRelation,
    WorkItemRelation,
    WorkItemRelationTypeEnum,
)

from plane_mcp.client import get_plane_client_context

# Relation type values accepted by the CE ``relations/`` endpoint.
_RELATION_TYPES: tuple[str, ...] = get_args(WorkItemRelationTypeEnum)


def register_work_item_relation_tools(mcp: FastMCP) -> None:
    """Register work item relation tools with the MCP server."""

    @mcp.tool()
    def list_work_item_relations(
        project_id: str,
        work_item_id: str,
    ) -> dict[str, Any]:
        """List every relation for a work item.

        Args:
            project_id: UUID of the project.
            work_item_id: UUID of the work item.

        Returns:
            Relations grouped by type (blocking, blocked_by, duplicate,
            relates_to, start_before, start_after, finish_before, finish_after).
        """
        client, workspace_slug = get_plane_client_context()
        relations = client.work_items.relations.list(
            workspace_slug=workspace_slug,
            project_id=project_id,
            work_item_id=work_item_id,
        )
        return relations.model_dump()

    @mcp.tool()
    def create_work_item_relation(
        project_id: str,
        work_item_id: str,
        work_item_ids: list[str],
        relation_type: str,
    ) -> list[WorkItemRelation]:
        """Relate a work item to one or more targets.

        Args:
            project_id: UUID of the project.
            work_item_id: UUID of the source work item.
            work_item_ids: UUIDs of the target work items.
            relation_type: One of blocking, blocked_by, duplicate, relates_to,
                start_before, start_after, finish_before, or finish_after.

        Returns:
            Details of the created relations.
        """
        client, workspace_slug = get_plane_client_context()
        if relation_type not in _RELATION_TYPES:
            raise ValueError(f"relation_type must be one of {list(_RELATION_TYPES)}.")
        data = CreateWorkItemRelation(
            relation_type=relation_type,  # type: ignore[arg-type]
            issues=work_item_ids,
        )
        response = client.work_items.relations._post(
            f"{workspace_slug}/projects/{project_id}/work-items/{work_item_id}/relations",
            data.model_dump(exclude_none=True),
        )
        return [WorkItemRelation.model_validate(item) for item in response]

    @mcp.tool()
    def remove_work_item_relation(
        project_id: str,
        work_item_id: str,
        related_work_item_id: str,
    ) -> None:
        """Remove ONE relation between two work items.

        Args:
            project_id: UUID of the project.
            work_item_id: UUID of the source work item.
            related_work_item_id: UUID of the related work item.
        """
        del project_id, work_item_id, related_work_item_id
        raise RuntimeError(
            "Removing work item relations is not available in the tested Plane Community Edition: "
            "it exposes only GET and POST on the relations endpoint."
        )
