# Contributing

Thanks for your interest in contributing to KADAS AI Integrations.

## Development Principles

- Keep components modular and composable.
- Prefer clear contracts for MCP tools and schemas.
- Keep geospatial assumptions explicit (CRS, extent, precision, data source).
- Prioritize reproducibility and testability.

## Local Development

- Preferred runtime for local validation: `C:\Program Files\KadasAlbireo\bin\python.exe`
- MCP client configuration: [.vscode/mcp.json](.vscode/mcp.json)
- Agent guidance: [skills/kadas-geospatial/SKILL.md](skills/kadas-geospatial/SKILL.md)

## Validation

- Run linting with `ruff check .`
- Run tests with `pytest`
- When changing MCP server wiring, verify that each server instantiates and registers tools correctly

## Pull Requests

- Open focused PRs with minimal unrelated changes.
- Include tests for new MCP tools when possible.
- Update README sections when adding or changing server capabilities.

## Documentation Expectations

- Document any new tool names and argument expectations.
- Note any assumptions about CRS, units, and remote services.
- Include fallback behavior when external APIs may fail.
