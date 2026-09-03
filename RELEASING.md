# Releasing `plane-community-mcp`

This fork is distributed on PyPI as **`plane-community-mcp`**. Its executable
remains **`plane-mcp-server-ce`**. The original `plane-mcp-server-ce` PyPI
project belongs to a different publisher, so users must install this fork by
its new distribution name.

## Before the first publication

1. Create or use the PyPI account that should own the project and enable 2FA.
2. Confirm the package name is unclaimed:

   ```bash
   curl -I https://pypi.org/pypi/plane-community-mcp/json
   ```

   A `404` means the first upload may create it. PyPI does not offer a separate
   package-registration step.
3. Create an **account-wide** PyPI API token for this first upload. A
   project-scoped token can only be created after the project exists.
4. In the GitHub repository, add that value as the Actions secret
   `PYPI_API_TOKEN`.

After the first successful release, replace the account-wide token with a token
scoped to `plane-community-mcp`, or configure PyPI Trusted Publishing for the
GitHub Actions workflow.

## Release checklist

1. Update `version` in `pyproject.toml` using a new PEP 440 version. PyPI never
   allows replacing an uploaded version.
2. Run the local release gate:

   ```bash
   rm -rf dist
   uv build
   uvx twine check dist/*
   uvx --from ./dist/plane_community_mcp-<version>-py3-none-any.whl \
     plane-mcp-server-ce --help
   ```

3. Commit the version change, push it, then run **Publish to PyPI** from the
   GitHub Actions tab. The workflow builds, validates, and uploads. GitHub
   releases are managed separately, so a PyPI recovery cannot alter an existing
   tag or release.
4. Verify the published artifact from a clean environment:

   ```bash
   uvx --refresh --from plane-community-mcp plane-mcp-server-ce --help
   ```

   A typical CE MCP configuration is:

   ```json
   {
     "command": "uvx",
     "args": ["--from", "plane-community-mcp", "plane-mcp-server-ce", "stdio"],
     "env": {
       "PLANE_BASE_URL": "https://your-plane.example",
       "PLANE_API_KEY": "<your-api-key>",
       "PLANE_WORKSPACE_SLUG": "<your-workspace>",
       "PLANE_MCP_EDITION": "community"
     }
   }
   ```
