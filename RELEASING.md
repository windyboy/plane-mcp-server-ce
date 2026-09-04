# Release

Package: `plane-community-mcp`
Command: `plane-mcp-server-ce`

## Checklist

1. Update `version` in `pyproject.toml`.
2. Run:

   ```bash
   uv sync --all-extras
   uv run ruff check .
   uv run pytest
   uv build
   uvx twine check dist/*
   ```

3. Commit, tag `v<version>`, and push the branch and tag.
4. Run the `Publish to PyPI` GitHub Actions workflow.
5. Create the matching GitHub Release.
6. Verify:

   ```bash
   uvx --refresh --from plane-community-mcp plane-mcp-server-ce --help
   ```

Publishing uses PyPI Trusted Publishing through `publish-pypi.yml`.
