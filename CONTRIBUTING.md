# Contributing

This project supports self-hosted Plane Community Edition.

## Report an issue

Include:

- Plane CE version and deployment method
- Python version and operating system
- MCP client and transport (`stdio` or HTTP)
- Minimal reproduction and relevant logs with secrets removed

Use the [issue tracker](https://github.com/windyboy/plane-mcp-server-ce/issues).

## Development

```bash
git clone https://github.com/windyboy/plane-mcp-server-ce.git
cd plane-mcp-server-ce
uv sync --all-extras
```

For live integration tests, copy `.env.test` to `.env.test.local` and provide
credentials for a CE instance. Do not commit that file.

```bash
uv run ruff check .
uv run pytest
```

## Changes

- Keep changes compatible with Plane CE.
- Add or update tests for behavior changes.
- Use typed tool parameters and register tools in `plane_mcp/tools/__init__.py`.
- Do not add Cloud-only, OAuth, or SSE support.
