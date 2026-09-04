# Plane MCP Server CE

MCP server for self-hosted Plane Community Edition.

- Package: `plane-community-mcp`
- Command: `plane-mcp-server-ce`
- Transports: stdio and Streamable HTTP with PAT headers
- OAuth and SSE are not supported.

## Install

```bash
uvx --from plane-community-mcp plane-mcp-server-ce --help
```

Python 3.10 or later is required.

## Stdio

Set the Plane URL, API key, and workspace slug:

```bash
export PLANE_BASE_URL="https://plane.example.com"
export PLANE_API_KEY="your-api-key"
export PLANE_WORKSPACE_SLUG="your-workspace"
export PLANE_MCP_EDITION="community"

uvx --from plane-community-mcp plane-mcp-server-ce stdio
```

Example MCP configuration:

```json
{
  "mcpServers": {
    "plane": {
      "command": "uvx",
      "args": ["--from", "plane-community-mcp", "plane-mcp-server-ce", "stdio"],
      "env": {
        "PLANE_BASE_URL": "https://plane.example.com",
        "PLANE_API_KEY": "your-api-key",
        "PLANE_WORKSPACE_SLUG": "your-workspace",
        "PLANE_MCP_EDITION": "community"
      }
    }
  }
}
```

## HTTP

Start the server:

```bash
export PLANE_BASE_URL="https://plane.example.com"
export PLANE_MCP_EDITION="community"
uvx --from plane-community-mcp plane-mcp-server-ce http
```

Endpoint:

```text
http://<host>:8211/http/api-key/mcp
```

Clients must send both headers:

```text
Authorization: Bearer <api-key>
x-workspace-slug: <workspace-slug>
```

Example with `mcp-remote`:

```json
{
  "mcpServers": {
    "plane": {
      "command": "npx",
      "args": [
        "mcp-remote@latest",
        "http://plane-mcp:8211/http/api-key/mcp",
        "--header", "Authorization: Bearer ${PLANE_API_KEY}",
        "--header", "x-workspace-slug: ${PLANE_WORKSPACE_SLUG}"
      ]
    }
  }
}
```

Docker:

```bash
docker build -t plane-mcp-server-ce .
docker run -p 8211:8211 \
  -e PLANE_BASE_URL="https://plane.example.com" \
  -e PLANE_MCP_EDITION="community" \
  plane-mcp-server-ce
```

## Configuration

| Variable | Required | Description |
| --- | --- | --- |
| `PLANE_BASE_URL` | Yes for self-hosted Plane | Plane instance origin. |
| `PLANE_API_KEY` | stdio | Personal API key. |
| `PLANE_WORKSPACE_SLUG` | stdio | Workspace slug. |
| `PLANE_MCP_EDITION` | Recommended | Set to `community` for CE-only tool discovery. |
| `PLANE_INTERNAL_BASE_URL` | No | Internal Plane URL for server-to-server calls. |
| `MCP_PATH_PREFIX` | No | HTTP route prefix. |
| `LOG_LEVEL` | No | Python log level; default `INFO`. |
| `LOG_USER_INFO` | No | Set to `true` to include display name in logs. |

### Session-only CE tools

CE exposes project pages and work-item archive operations through its app API,
not the public API. Enable these tools with either a session cookie or login
credentials:

```bash
export PLANE_SESSION_COOKIE="<session-id-cookie>"
# Or:
export PLANE_SESSION_EMAIL="you@example.com"
export PLANE_SESSION_PASSWORD="your-password"
```

Without these variables, session-only tools are hidden. Prefer a session cookie
over an account password. The cookie is the `session-id` value from an active
browser session and must be replaced when it expires.

On Plane Cloud, page create, update, archive, unarchive, and delete use the
public SDK/API path. On CE, page updates preserve the app API's separate name
and content routes; `update_page` accepts either or both fields.

## CE scope

CE mode exposes supported projects, work items, cycles, modules, labels,
states, comments, links, attachments, activities, and project pages. Unsupported
or partial endpoints are omitted from discovery where possible. See
[CE_COMPAT.md](CE_COMPAT.md) for endpoint evidence and the complete matrix.

## Logging

Logs are JSON. Each tool call emits one success or error event with the tool
name and duration. Request payloads are not logged.

## Development

```bash
uv sync --all-extras
uv run ruff check .
uv run pytest
```

## Release

See [RELEASING.md](RELEASING.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
