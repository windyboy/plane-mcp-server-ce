# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Plane MCP Server — a Python-based Model Context Protocol server that exposes Plane's project management API as MCP tools. Built on FastMCP with the official `plane-sdk`. Supports two transport modes: stdio (local) and HTTP (PAT header auth). OAuth and SSE transports were removed: Plane CE exposes no OAuth provider endpoints, so those flows could never work self-hosted.

## Common Commands

```bash
# Install dependencies (uses uv)
uv pip install -e ".[dev]"

# Run the server locally (stdio mode)
PLANE_API_KEY=... PLANE_WORKSPACE_SLUG=... python -m plane_mcp stdio

# Run HTTP server
python -m plane_mcp http

# Run all tests
pytest

# Run a single test
pytest tests/test_integration.py::test_full_integration -v

# Run tests with env vars from file
export $(cat .env.test.local | xargs) && pytest tests/ -v

# Format code (line length: 120)
ruff format plane_mcp/

# Lint (rules: E, F, I, UP, B; line length: 120)
ruff check plane_mcp/
```

## Architecture

### Entry Point & Transport Modes

`plane_mcp/__main__.py` parses a positional arg (`stdio` or `http`) and launches the corresponding server:
- **stdio**: Requires `PLANE_API_KEY` + `PLANE_WORKSPACE_SLUG` env vars. Runs locally.
- **http**: Starts on port 8211 with a PAT-header endpoint at `/http/api-key/mcp`.

### Server Factories (`server.py`)

Two factory functions (`get_header_mcp`, `get_stdio_mcp`) each create a `FastMCP` instance, register all tools, and configure the appropriate auth.

### Client Context (`client.py`)

`get_plane_client_context()` returns a `PlaneClientContext(client, workspace_slug)` namedtuple. It resolves credentials from the MCP request context (header API key) or from environment variables (stdio mode). Prefers `PLANE_INTERNAL_BASE_URL` for server-to-server calls.

### Authentication (`auth/`)

- `PlaneHeaderAuthProvider` — Token middleware auth: the API key arrives as `Authorization: Bearer`, the workspace as the `x-workspace-slug` header; the key is validated against Plane's `/api/v1/users/me/`.

### Tools (`tools/`)

19 tool modules organized by Plane domain (projects, work_items, cycles, modules, etc.), totaling 55+ tools. Each module exports a `register_*_tools(mcp: FastMCP)` function called from `tools/__init__.py`.

**Tool pattern:**
```python
def register_*_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def tool_name(param: str, optional_param: str | None = None) -> SomePlaneModel:
        """Docstring with Args and Returns sections."""
        client, workspace_slug = get_plane_client_context()
        return client.endpoint.operation(workspace_slug=workspace_slug, ...)
```

Tools return Pydantic models from `plane-sdk` and use Python 3.10+ union syntax (`str | None`).

### Testing

Integration tests in `tests/test_integration.py` use `FastMCP.Client` with `StreamableHttpTransport`. Tests run against a live Plane instance — configure via `.env.test` (copy to `.env.test.local` with real values).

## Key Environment Variables

| Variable | Required For | Purpose |
|---|---|---|
| `PLANE_API_KEY` | stdio | API key for authentication |
| `PLANE_WORKSPACE_SLUG` | stdio | Target workspace |
| `PLANE_BASE_URL` | all (default: https://api.plane.so) | Plane API URL |
| `PLANE_INTERNAL_BASE_URL` | http (optional) | Internal URL for server-to-server calls |
| `LOG_USER_INFO` | all (optional, default: false) | When `true`, include user info (PII such as display name) in logs alongside the opaque user id |
