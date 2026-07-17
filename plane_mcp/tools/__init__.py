"""Tools for Plane MCP Server."""

import os
from urllib.parse import urlparse

from fastmcp import FastMCP

from plane_mcp.tools.cycles import register_cycle_tools
from plane_mcp.tools.initiatives import register_initiative_tools
from plane_mcp.tools.intake import register_intake_tools
from plane_mcp.tools.labels import register_label_tools
from plane_mcp.tools.milestones import register_milestone_tools
from plane_mcp.tools.modules import register_module_tools
from plane_mcp.tools.pages import register_page_tools
from plane_mcp.tools.pql import register_pql_tools
from plane_mcp.tools.projects import register_project_tools
from plane_mcp.tools.roles import register_role_tools
from plane_mcp.tools.states import register_state_tools
from plane_mcp.tools.users import register_user_tools
from plane_mcp.tools.work_item_activities import register_work_item_activity_tools
from plane_mcp.tools.work_item_attachments import register_work_item_attachment_tools
from plane_mcp.tools.work_item_comments import register_work_item_comment_tools
from plane_mcp.tools.work_item_links import register_work_item_link_tools
from plane_mcp.tools.work_item_properties import register_work_item_property_tools
from plane_mcp.tools.work_item_relation_definitions import register_work_item_relation_definition_tools
from plane_mcp.tools.work_item_relations import register_work_item_relation_tools
from plane_mcp.tools.work_item_types import register_work_item_type_tools
from plane_mcp.tools.work_items import register_work_item_tools
from plane_mcp.tools.work_logs import register_work_log_tools
from plane_mcp.tools.workspaces import register_workspace_tools

# These endpoints are not registered by Plane Community Edition.  Keeping them
# out of MCP discovery is more useful than exposing tools that can only return
# a 404.  See CE_COMPAT.md for the endpoint-by-endpoint evidence.
CE_UNAVAILABLE_TOOLS = frozenset(
    {
        "get_features",
        "update_workspace_features",
        "update_project_features",
        "get_project_worklog_summary",
        "get_project_estimate",
        "list_project_estimate_points",
        "create_project_estimate",
        "update_project_estimate",
        "delete_project_estimate",
        "link_estimate_to_project",
        "create_project_estimate_points",
        "update_project_estimate_point",
        "delete_project_estimate_point",
        "count_work_items",
        "list_archived_work_items",
        "remove_work_item_relation",
        "list_work_item_relation_definitions",
        "create_work_item_relation_definition",
        "update_work_item_relation_definition",
        "delete_work_item_relation_definition",
        "list_work_logs",
        "create_work_log",
        "update_work_log",
        "delete_work_log",
        "list_initiatives",
        "create_initiative",
        "retrieve_initiative",
        "update_initiative",
        "delete_initiative",
        "list_initiative_projects",
        "manage_initiative_projects",
        "list_milestones",
        "create_milestone",
        "retrieve_milestone",
        "update_milestone",
        "delete_milestone",
        "manage_milestone_work_items",
        "list_milestone_work_items",
        "list_roles",
        "retrieve_role",
        "list_pages",
        "attach_page_to_work_item",
        "list_work_item_pages",
        "detach_page_from_work_item",
        "retrieve_page",
        "create_page",
        "list_work_item_types",
        "create_work_item_type",
        "import_work_item_types_to_project",
        "resolve_work_item_type",
        "retrieve_work_item_type",
        "update_work_item_type",
        "delete_work_item_type",
        "get_work_item_property_value",
        "set_work_item_property_value",
        "delete_work_item_property_value",
    }
)


def is_community_edition() -> bool:
    """Whether MCP discovery should expose only CE-compatible tools.

    ``PLANE_MCP_EDITION`` accepts ``community``/``ce`` to force CE mode and
    ``cloud`` to expose the complete SDK surface.  Its default, ``auto``,
    treats a configured non-``*.plane.so`` API host as self-hosted.  Explicit
    configuration is recommended for custom Cloud domains.
    """
    edition = os.getenv("PLANE_MCP_EDITION", "auto").strip().lower()
    if edition in {"community", "ce"}:
        return True
    if edition in {"cloud", "all"}:
        return False
    if edition != "auto":
        raise ValueError("PLANE_MCP_EDITION must be one of: auto, community (or ce), cloud (or all).")

    base_url = os.getenv("PLANE_INTERNAL_BASE_URL") or os.getenv("PLANE_BASE_URL", "")
    hostname = urlparse(base_url).hostname or ""
    return bool(hostname) and not hostname.endswith(".plane.so") and hostname != "plane.so"


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the MCP server."""
    ce_mode = is_community_edition()
    register_project_tools(mcp)
    register_work_item_tools(mcp, supports_pql=not ce_mode)
    register_work_item_activity_tools(mcp)
    register_work_item_attachment_tools(mcp)
    register_work_item_comment_tools(mcp)
    register_work_item_link_tools(mcp)
    register_work_item_relation_definition_tools(mcp)
    register_work_item_relation_tools(mcp)
    register_work_log_tools(mcp)
    register_cycle_tools(mcp)
    register_user_tools(mcp)
    register_module_tools(mcp)
    register_initiative_tools(mcp)
    register_intake_tools(mcp)
    register_label_tools(mcp)
    register_page_tools(mcp)
    register_work_item_property_tools(mcp)
    register_work_item_type_tools(mcp)
    register_state_tools(mcp)
    register_workspace_tools(mcp)
    register_milestone_tools(mcp)
    register_role_tools(mcp)
    register_pql_tools(mcp)

    if ce_mode:
        for tool_name in CE_UNAVAILABLE_TOOLS:
            mcp.local_provider.remove_tool(tool_name)
