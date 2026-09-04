# Plane MCP Server CE

> [!IMPORTANT]
> ## Community Edition and self-hosted first
>
> This fork exists to provide the broadest possible MCP compatibility with the
> free, self-hosted **Plane Community Edition**. It is not intended for upstream
> contribution: its focus is making every capability that CE actually exposes
> usable by AI agents, while keeping Cloud-only and paid features out of their
> tool list.
>
> Issues and pull requests that improve Plane CE or self-hosted compatibility
> are warmly welcome. Contributions authored with AI coding agents are welcome
> too, provided they are clean, reviewed, and remain aligned with this CE and
> self-hosted focus.

A Model Context Protocol (MCP) server for Plane integration. This package is
published on PyPI as `plane-community-mcp` and provides tools and resources for
interacting with self-hosted Plane CE through AI agents. The distribution name
is intentionally different from the executable: install
`plane-community-mcp`, then run `plane-mcp-server-ce`.

This repository is a fork of `plane-mcp-server-ce`. It publishes under its own
distribution name because the PyPI project `plane-mcp-server-ce` belongs to the
upstream project; the GitHub repository and the CLI command keep the original
name so existing agent configurations keep working.

## Features

* 🏠 **CE-first**: hides API surfaces that self-hosted Community Edition cannot serve.
* 🔐 **Two credential paths**: PAT/SDK for the public API; a browser session for the CE app-API features (pages, archive).
* 📄 **Useful Pages support**: CE project pages support create, retrieve, rename, HTML content updates, archive, unarchive, and archived-page deletion.
* 🔌 **Multiple transports**: stdio, SSE, and streamable HTTP.

## Usage

The server supports three transport methods. **We recommend using `uvx`** as it doesn't require installation.

### Install name vs. run command

The PyPI distribution is `plane-community-mcp`, while the executable remains
`plane-mcp-server-ce`. Use both names when starting it with `uvx`:

```bash
uvx --from plane-community-mcp plane-mcp-server-ce --help
```

Do not use `uvx plane-community-mcp`: that is the installable distribution, not
the executable name. If you prefer a persistent installation instead:

```bash
python -m pip install plane-community-mcp
plane-mcp-server-ce stdio
```

**Requirements**:
- **Python 3.10+** (for stdio transport, via `uvx`)
- **Node.js 22+** (for remote transports, via `npx`)

### 1. Stdio transport against self-hosted Plane CE (recommended)

This is the standard setup for a self-hosted Community Edition instance. Set
the environment variables before launching the server:

```bash
export PLANE_BASE_URL="https://your-plane.example"   # your CE instance origin
export PLANE_API_KEY="your-api-key"                  # created in CE workspace settings → API
export PLANE_WORKSPACE_SLUG="your-workspace"
export PLANE_MCP_EDITION="community"

# Session credentials — required for the CE-only tools this fork exists for
# (project pages, work-item archive/unarchive). Everything else works with
# the API key alone; without these, pages and archive tools stay hidden.
# export PLANE_SESSION_COOKIE="<session-id cookie value>"   # preferred
# … or email + password instead of a cookie:
# export PLANE_SESSION_EMAIL="you@example.com"
# export PLANE_SESSION_PASSWORD="your-password"

uvx --from plane-community-mcp plane-mcp-server-ce stdio
```

Project pages and work-item archiving are the reason to run this fork instead
of upstream — and they **require** session credentials: without `PLANE_SESSION_*`
those tools stay hidden, while the rest of the server works with the API key
alone. See [Session-only capabilities](#session-only-capabilities-community-edition)
for how to obtain the cookie.

**MCP Client Configuration** (using uvx - recommended):

```json
{
  "mcpServers": {
    "plane": {
      "command": "uvx",
      "args": ["--from", "plane-community-mcp", "plane-mcp-server-ce", "stdio"],
      "env": {
        "PLANE_API_KEY": "<your-api-key>",
        "PLANE_WORKSPACE_SLUG": "<your-workspace-slug>",
        "PLANE_BASE_URL": "https://<your-self-hosted-plane-url>",
        "PLANE_MCP_EDITION": "community",
        "PLANE_SESSION_COOKIE": "<your-session-id-cookie>"
      }
    }
  }
}
```

The `PLANE_SESSION_COOKIE` entry (or `PLANE_SESSION_EMAIL` +
`PLANE_SESSION_PASSWORD`) is what turns on the pages and archive tools —
the CE features this fork exists for. Omit it and those tools stay hidden.

### 2. Self-hosted HTTP transports

Run the server on your own network when several clients need to reach it over
HTTP, or when your client only speaks URL-based transports. The server listens
on port **8211** and mounts three endpoints:

| Endpoint | Transport | Authentication |
|---|---|---|
| `/http/api-key/mcp` | Streamable HTTP | PAT headers (`x-api-key` + `x-workspace-slug`) |
| `/http/mcp` | Streamable HTTP | OAuth |
| `/sse` | SSE (legacy) | OAuth |

#### PAT (header) mode — the simple option for CE

The server only needs to know where your Plane instance lives; each client
authenticates with its own API key:

```bash
export PLANE_BASE_URL="https://your-plane.example"
export PLANE_MCP_EDITION="community"
uvx --from plane-community-mcp plane-mcp-server-ce http
```

Or with Docker (the image defaults to the `http` transport):

```bash
docker build -t plane-mcp-server-ce .
docker run -p 8211:8211 \
  -e PLANE_BASE_URL="https://your-plane.example" \
  -e PLANE_MCP_EDITION="community" \
  plane-mcp-server-ce
```

Client configuration (`mcp-remote` forwards the headers; `${VAR}` is expanded
from the client's environment):

```json
{
  "mcpServers": {
    "plane": {
      "command": "npx",
      "args": [
        "mcp-remote@latest",
        "http://your-server:8211/http/api-key/mcp",
        "--header", "x-api-key:${PLANE_API_KEY}",
        "--header", "x-workspace-slug:${PLANE_WORKSPACE_SLUG}"
      ]
    }
  }
}
```

#### OAuth mode

OAuth requires a Plane OAuth client. Set `PLANE_OAUTH_PROVIDER_CLIENT_ID`,
`PLANE_OAUTH_PROVIDER_CLIENT_SECRET`, and `PLANE_OAUTH_PROVIDER_BASE_URL` (the
public base URL of this MCP server, e.g. `https://mcp.example.com`) before
starting the `http` transport, then point clients at `http://your-server:8211/http/mcp`.
OAuth tokens are kept in memory by default and are lost on restart; set
`REDIS_HOST` / `REDIS_PORT` (and `REDIS_PASSWORD` if required) to persist them.

#### SSE (legacy)

The legacy SSE endpoint is served at `http://your-server:8211/sse` with the
same OAuth setup as above. Prefer the HTTP endpoints for new clients.

### 3. Plane Cloud hosted server (official)

The sections above cover self-hosted Community Edition. Plane also operates a
hosted MCP server at `mcp.plane.so` for Plane Cloud workspaces — those
endpoints belong to the official service, not to this fork, and none of the
CE-specific behavior applies when connecting to them. Configuration for
clients without native remote MCP support:

**OAuth**: `https://mcp.plane.so/http/mcp`

```json
{
  "mcpServers": {
    "plane": {
      "command": "npx",
      "args": ["mcp-remote@latest", "https://mcp.plane.so/http/mcp"]
    }
  }
}
```

**PAT headers**: `https://mcp.plane.so/http/api-key/mcp`

```json
{
  "mcpServers": {
    "plane": {
      "command": "npx",
      "args": [
        "mcp-remote@latest",
        "https://mcp.plane.so/http/api-key/mcp",
        "--header", "Authorization: Bearer ${PLANE_PAT_TOKEN}",
        "--header", "X-Workspace-slug: ${PLANE_WORKSPACE_SLUG}"
      ]
    }
  }
}
```

**SSE (legacy)**: `https://mcp.plane.so/sse`

```json
{
  "mcpServers": {
    "plane": {
      "command": "npx",
      "args": ["mcp-remote@latest", "https://mcp.plane.so/sse"]
    }
  }
}
```

OAuth authentication is handled automatically when connecting to the hosted
server.


## Configuration

### Authentication

The server requires authentication via environment variables:

- `PLANE_BASE_URL`: Base URL for Plane API (default: `https://api.plane.so`). For self-hosted CE, set this to your instance origin, e.g. `https://your-plane.example`.
- `PLANE_API_KEY`: API key for authentication (required for stdio transport)
- `PLANE_WORKSPACE_SLUG`: Workspace slug identifier (required for stdio transport)
- `PLANE_INTERNAL_BASE_URL`: Internal URL preferred over `PLANE_BASE_URL` for server-to-server calls (useful when the MCP server runs inside the same network as Plane). Also consulted by `PLANE_MCP_EDITION=auto` when detecting a self-hosted instance.
- `PLANE_MCP_EDITION`: Tool discovery mode: `community` (or `ce`) exposes only
  tools verified against Plane CE; `cloud` (or `all`) exposes the complete SDK
  surface; `auto` is the default and treats a configured non-`*.plane.so` API
  URL as self-hosted. Set `community` explicitly for predictable self-hosted
  deployments, especially if you use a custom Cloud domain.
- `PLANE_SESSION_EMAIL` / `PLANE_SESSION_PASSWORD`, or `PLANE_SESSION_COOKIE`:
  CE-only app-session credentials — required for the tools this fork exists
  for (work-item archive/unarchive and project pages); without them those
  tools are hidden from discovery. See
  [Session-only capabilities](#session-only-capabilities-community-edition).

**Example** (self-hosted CE, stdio transport):
```bash
export PLANE_BASE_URL="https://your-plane.example"
export PLANE_API_KEY="your-api-key"
export PLANE_WORKSPACE_SLUG="your-workspace-slug"
export PLANE_MCP_EDITION="community"
```

**Note**: For the self-hosted HTTP transports (section 2), set `PLANE_BASE_URL` (and `PLANE_MCP_EDITION`) on the *server*; each client then authenticates via OAuth or PAT headers. For the hosted Plane Cloud server (section 3), authentication is handled by the connection method (OAuth flow or PAT headers) and needs none of these environment variables.

### OAuth redirect URIs

For the OAuth HTTP/SSE transports, the server validates each client's redirect URI against an allowlist. Common MCP clients (Cursor, VS Code, Claude.ai, ChatGPT connectors, localhost) are allowed by default.

To onboard a new client without a code change or release, append extra patterns via an environment variable:

- `PLANE_OAUTH_ALLOWED_REDIRECT_URIS`: Comma-separated redirect URI patterns appended to the built-in allowlist.

```bash
export PLANE_OAUTH_ALLOWED_REDIRECT_URIS="https://newclient.com/cb,https://other.app/oauth/*"
```

Patterns support glob matching (`*` matches any port, path segment, or subdomain). For security, keep the host pinned and wildcard only the port/path.

### Logging

The server emits structured JSON logs. Each tool call is logged with its tool name, duration, status, and (when available) the opaque user id and workspace slug.

- `LOG_USER_INFO`: When `true`, include user info (PII such as the display name) in logs alongside the opaque user id. Defaults to `false` so PII is never logged unless explicitly opted in. Only the OAuth and PAT (header) HTTP transports carry a display name; stdio is unaffected.

```bash
export LOG_USER_INFO="true"
```

## Available Tools

The server provides comprehensive tools for interacting with Plane. All tools use Pydantic models from the Plane SDK for type safety and validation.

### Community Edition availability

Set `PLANE_MCP_EDITION=community` to prevent unavailable tools from being
advertised to an agent. This keeps the MCP tool list focused on functionality
that exists on the free, self-hosted edition instead of returning cryptic 404
errors. The detailed endpoint evidence is maintained in [CE_COMPAT.md](CE_COMPAT.md).

| Capability group | Available in CE mode | Notes |
|---|---:|---|
| Projects, members, cycles, modules, labels, states, intake items | Yes | CE-compatible endpoints, including the CE fallback for `*-lite` lists. |
| Work items, search, activities, comments, links, attachments | Yes | Detail reads automatically expand assignees and labels. `list_work_items` deliberately does **not** expose `pql` in CE mode: the CE API silently ignores it. |
| Work item relations | Partial | Listing and creating the eight built-in relation types work; CE stable exposes no deletion route. |
| Work item property definitions and options | Partial | Definition tools remain exposed; per-item property values are not available. |
| Feature flags, roles, initiatives, milestones | No | Cloud-only / paid API surface. |
| Work logs, estimates | No | Endpoints are absent from the tested CE API. |
| Work item archive/unarchive, archived work items | Session | Absent from the public API; reachable through the app API when app-session credentials are configured (see below). |
| Project pages | Session | Root-project pages can create, retrieve, rename, update HTML, archive, unarchive, and delete archived pages through the app API. Workspace pages and work-item↔page links have no CE route. |
| Work item types, custom relation definitions | No | Endpoints are absent from the tested CE API. |

The category tables below describe the full SDK surface. Rows marked **No** or
**Partial** above are deliberately omitted from MCP discovery in Community
Edition mode. Rows marked **Session** are hidden by default and exposed only
when app-session credentials are set.

### Session-only capabilities (Community Edition)

A few things exist on a self-hosted CE instance but are served only by the
internal *app* API (`/api/…`, no `/v1`), which uses a browser session and
rejects a personal access token with `401`: **work-item archive/unarchive**
(and listing archived items) and **project pages**.

Provide app-session credentials to unlock them. The MCP then logs in like the
web app (CSRF + `/auth/sign-in/`), reuses the session cookie, and routes only
these tools through the app API; everything else keeps using your PAT. On Plane
Cloud these variables are ignored.

```bash
# either email + password …
export PLANE_SESSION_EMAIL="you@example.com"
export PLANE_SESSION_PASSWORD="your-password"
# … or a pre-obtained session cookie (keeps the password out of the environment)
export PLANE_SESSION_COOKIE="<session-id cookie value>"
```

To get the cookie: log into your CE instance in the browser, then copy the
`session-id` value from DevTools → Application → Cookies. It expires when you
log out or the session is invalidated — when the pages and archive tools start
returning `401`, copy a fresh one. Email + password avoids expiry but places
your full account credentials in the environment; prefer the cookie.

Pages available with a session are deliberately small and predictable:

| Tool | CE behavior |
|---|---|
| `create_page` | Creates a project page, writes `description_html`, then reads it back. |
| `update_page` / `update_page_content` | Rename a root-project page or replace its HTML content. |
| `archive_page` / `unarchive_page` | Archive or restore a root-project page and return the read-back page. |
| `delete_page` | Deletes an **already archived** project page. Archive first; CE rejects deletion of active pages. |

Notes:
- These credentials are your full user login (the app API is more privileged
  than a scoped PAT). Prefer `PLANE_SESSION_COOKIE` where possible.
- Only **project** pages are available; workspace-level pages and
  work-item↔page links have no CE endpoint and stay hidden.
- Page writes are conservative: they are never automatically replayed. A 4xx
  means the request was rejected; a 5xx or transport failure may be ambiguous,
  so retrieve the page before retrying.
- These four mutations are CE-only and intentionally do not appear in Cloud
  discovery: `update_page`, `update_page_content`, `archive_page`, and
  `unarchive_page`. Cloud retains `delete_page` through the SDK.
- Without these variables, the affected tools stay hidden in CE mode (no cryptic
  404s). The endpoint evidence is in [CE_COMPAT.md](CE_COMPAT.md).

### Projects

| Tool Name | Description |
|-----------|-------------|
| `list_projects` | List all projects in a workspace with optional pagination and filtering |
| `create_project` | Create a new project with name, identifier, and optional configuration |
| `retrieve_project` | Retrieve a project by ID |
| `update_project` | Update a project with partial data |
| `delete_project` | Delete a project by ID |
| `get_project_worklog_summary` | Get work log summary for a project |
| `get_project_members` | Get all members of a project |
| `update_project_features` | Update features configuration of a project |

### Work Items

| Tool Name | Description |
|-----------|-------------|
| `list_work_items` | List all work items in a project with pagination. In Community Edition mode, server-side PQL filtering is unavailable and is not exposed to agents. |
| `create_work_item` | Create a new work item with name, assignees, labels, and other attributes |
| `retrieve_work_item` | Retrieve a work item by ID with optional field expansion |
| `retrieve_work_item_by_identifier` | Retrieve a work item by project identifier and issue sequence number |
| `update_work_item` | Update a work item with partial data |
| `delete_work_item` | Delete a work item by ID |
| `search_work_items` | Search work items across a workspace with query string |

### Cycles

| Tool Name | Description |
|-----------|-------------|
| `list_cycles` | List cycles in a project (set `archived=true` for archived) |
| `create_cycle` | Create a new cycle with name, dates, and owner |
| `retrieve_cycle` | Retrieve a cycle by ID |
| `update_cycle` | Update a cycle with partial data |
| `delete_cycle` | Delete a cycle by ID |
| `manage_cycle_work_items` | Add and/or remove work items on a cycle |
| `list_cycle_work_items` | List work items in a cycle |
| `transfer_cycle_work_items` | Transfer work items from one cycle to another |
| `manage_cycle_archive` | Archive or unarchive a cycle |

### Modules

| Tool Name | Description |
|-----------|-------------|
| `list_modules` | List modules in a project (set `archived=true` for archived) |
| `create_module` | Create a new module with name, dates, status, and members |
| `retrieve_module` | Retrieve a module by ID |
| `update_module` | Update a module with partial data |
| `delete_module` | Delete a module by ID |
| `manage_module_work_items` | Add and/or remove work items on a module |
| `list_module_work_items` | List work items in a module |
| `manage_module_archive` | Archive or unarchive a module |

### Initiatives

| Tool Name | Description |
|-----------|-------------|
| `list_initiatives` | List all initiatives in a workspace |
| `create_initiative` | Create a new initiative with name, dates, state, and lead |
| `retrieve_initiative` | Retrieve an initiative by ID |
| `update_initiative` | Update an initiative with partial data |
| `delete_initiative` | Delete an initiative by ID |

### Intake Work Items

| Tool Name | Description |
|-----------|-------------|
| `list_intake_work_items` | List all intake work items in a project with optional pagination |
| `create_intake_work_item` | Create a new intake work item in a project |
| `retrieve_intake_work_item` | Retrieve an intake work item by work item ID with optional field expansion |
| `update_intake_work_item` | Update an intake work item with partial data |
| `delete_intake_work_item` | Delete an intake work item by work item ID |

### Work Item Properties

| Tool Name | Description |
|-----------|-------------|
| `list_work_item_properties` | List work item properties for a work item type |
| `create_work_item_property` | Create a new work item property with type, settings, and validation rules |
| `retrieve_work_item_property` | Retrieve a work item property by ID |
| `update_work_item_property` | Update a work item property with partial data |
| `delete_work_item_property` | Delete a work item property by ID |

### Milestones

| Tool Name | Description |
|-----------|-------------|
| `list_milestones` | List all milestones in a project |
| `create_milestone` | Create a new milestone |
| `retrieve_milestone` | Retrieve a milestone by ID |
| `update_milestone` | Update a milestone by ID |
| `delete_milestone` | Delete a milestone by ID |
| `manage_milestone_work_items` | Add and/or remove work items on a milestone |
| `list_milestone_work_items` | List work items in a milestone |

### Labels

| Tool Name | Description |
|-----------|-------------|
| `list_labels` | List all labels in a project |
| `create_label` | Create a new label |
| `retrieve_label` | Retrieve a label by ID |
| `update_label` | Update a label by ID |
| `delete_label` | Delete a label by ID |

### States

| Tool Name | Description |
|-----------|-------------|
| `list_states` | List all states in a project |
| `create_state` | Create a new state |
| `retrieve_state` | Retrieve a state by ID |
| `update_state` | Update a state by ID |
| `delete_state` | Delete a state by ID |

### Work Item Comments

| Tool Name | Description |
|-----------|-------------|
| `list_work_item_comments` | List comments for a work item |
| `retrieve_work_item_comment` | Retrieve a specific comment for a work item |
| `create_work_item_comment` | Create a comment for a work item |
| `update_work_item_comment` | Update a comment for a work item |
| `delete_work_item_comment` | Delete a comment for a work item |

### Work Item Links

| Tool Name | Description |
|-----------|-------------|
| `list_work_item_links` | List links for a work item |
| `retrieve_work_item_link` | Retrieve a specific link for a work item |
| `create_work_item_link` | Create a link for a work item |
| `update_work_item_link` | Update a link for a work item |
| `delete_work_item_link` | Delete a link for a work item |

### Work Item Types

| Tool Name | Description |
|-----------|-------------|
| `list_work_item_types` | List all work item types in a project |
| `create_work_item_type` | Create a new work item type |
| `retrieve_work_item_type` | Retrieve a work item type by ID |
| `update_work_item_type` | Update a work item type by ID |
| `delete_work_item_type` | Delete a work item type by ID |
| `import_work_item_types_to_project` | Bulk-link workspace-level work item types to a project |
| `resolve_work_item_type` | Find or create a named type for a project, auto-handling workspace vs project scope and import |

### Work Item Relations

| Tool Name | Description |
|-----------|-------------|
| `list_work_item_relations` | List relations for a work item |
| `create_work_item_relation` | Create relations for a work item |
| `remove_work_item_relation` | Remove a relation from a work item |

### Work Item Relation Definitions

| Tool Name | Description |
|-----------|-------------|
| `list_work_item_relation_definitions` | List workspace custom relation definitions |
| `create_work_item_relation_definition` | Create a workspace relation definition |
| `update_work_item_relation_definition` | Update a relation definition |
| `delete_work_item_relation_definition` | Delete a relation definition |

### Work Item Activities

| Tool Name | Description |
|-----------|-------------|
| `list_work_item_activities` | List activities for a work item |
| `retrieve_work_item_activity` | Retrieve a specific activity for a work item |

### Work Logs

| Tool Name | Description |
|-----------|-------------|
| `list_work_logs` | List work logs for a work item |
| `create_work_log` | Create a work log for a work item |
| `update_work_log` | Update a work log for a work item |
| `delete_work_log` | Delete a work log for a work item |

### Pages

| Tool Name | Description |
|-----------|-------------|
| `list_pages` | List pages (workspace, or a project's if `project_id` given) |
| `retrieve_page` | Retrieve a page by ID (workspace, or project's if `project_id` given) |
| `create_page` | Create a workspace or project page |

### Workspaces

| Tool Name | Description |
|-----------|-------------|
| `get_workspace_members` | Get all members of the current workspace |
| `get_features` | Get feature flags (workspace, or a project's if `project_id` given) |
| `update_workspace_features` | Update features of the current workspace |

### Users

| Tool Name | Description |
|-----------|-------------|
| `get_me` | Get current authenticated user information |

**Total Tools**: 100+ tools across 20 categories

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black plane_mcp/
ruff check plane_mcp/
```

## License

MIT License - see LICENSE for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Deprecation Notice

⚠️ **The Node.js-based `plane-mcp-server` is deprecated and no longer maintained.**

This repository represents the new Python+FastMCP based implementation of the Plane MCP server. If you were using the previous Node.js version, please migrate to this Python-based version for continued support and updates.

The new implementation offers:
- Better type safety with Pydantic models
- Improved performance with FastMCP
- Enhanced tool coverage
- Active maintenance and development

For migration assistance, please refer to the configuration examples in this README or open an issue for support.

**Old Node.js Configuration (Deprecated):**

If you were using the previous Node.js-based `@makeplane/plane-mcp-server`, your configuration looked like this:

```json
{
  "mcpServers": {
    "plane": {
      "command": "npx",
      "args": [
        "-y",
        "@makeplane/plane-mcp-server"
      ],
      "env": {
        "PLANE_API_KEY": "<YOUR_API_KEY>",
        "PLANE_API_HOST_URL": "<HOST_URL_FOR_SELF_HOSTED>",
        "PLANE_WORKSPACE_SLUG": "<YOUR_WORKSPACE_SLUG>"
      }
    }
  }
}
```

**Please migrate to the new Python-based configuration shown in the Usage section above.**

## Releasing `plane-community-mcp`

Maintainers should follow [RELEASING.md](RELEASING.md). The PyPI distribution
is `plane-community-mcp`; the executable remains `plane-mcp-server-ce`.
Publishing uses PyPI Trusted Publishing, so no PyPI token is stored in this
repository.
