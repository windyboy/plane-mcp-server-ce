# Repository guidance

## Scope

Python MCP server for self-hosted Plane Community Edition.

- FastMCP 4
- stdio and PAT-header Streamable HTTP
- No Cloud-only, OAuth, or SSE support

## Commands

```bash
uv sync --all-extras
uv run plane-mcp-server-ce stdio
uv run plane-mcp-server-ce http
uv run ruff format .
uv run ruff check .
uv run pytest
```

Live integration tests require `.env.test.local`; do not commit it.

## Architecture

- `plane_mcp/__main__.py`: CLI and HTTP ASGI application.
- `plane_mcp/server.py`: stdio and HTTP FastMCP factories.
- `plane_mcp/auth/plane_header_auth_provider.py`: PAT verification for HTTP.
- `plane_mcp/client.py`: Plane SDK client and request/environment credentials.
- `plane_mcp/tools/`: tool registration and CE filtering.
- `plane_mcp/app_session.py`: CE app-session support for pages and archive tools.

## Conventions

- Use typed tool parameters and return Plane SDK models where applicable.
- Register new tools in `plane_mcp/tools/__init__.py`.
- Keep unavailable CE endpoints out of discovery.
- Add tests for behavior changes.
- Use Ruff; line length is 120.
