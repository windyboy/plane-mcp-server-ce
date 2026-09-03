# Releasing `plane-community-mcp`

This fork is distributed on PyPI as **`plane-community-mcp`**. Its executable
remains **`plane-mcp-server-ce`**. The original `plane-mcp-server-ce` PyPI
project belongs to a different publisher, so users must install this fork by
its new distribution name.

## Trusted Publishing setup

This repository publishes through PyPI Trusted Publishing (GitHub OIDC). No
PyPI API token or `PYPI_API_TOKEN` GitHub secret is needed.

For the first publication:

1. Create or use the PyPI account that should own the project, verify its email,
   and enable 2FA.
2. In PyPI, open **Account settings → Publishing**, choose **GitHub Actions**,
   and add a pending publisher with:

   - PyPI project name: `plane-community-mcp`
   - Owner: `windyboy`
   - Repository: `plane-mcp-server-ce`
   - Workflow filename: `publish-pypi.yml`
   - Environment: leave blank (the workflow does not use a GitHub Environment)

3. Confirm the package name is still unclaimed:

   ```bash
   curl -I https://pypi.org/pypi/plane-community-mcp/json
   ```

   A `404` is expected. A pending publisher does not reserve the name; the
   first successful workflow run creates the project and activates the
   publisher.

After the first successful release, the pending publisher becomes a normal
publisher. Future releases require no additional PyPI credential setup.

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
   GitHub Actions tab. The workflow builds and validates in a read-only job,
   then uploads in a separate OIDC-authorized job. GitHub releases are managed
   separately, so a PyPI recovery cannot alter an existing tag or release.
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
