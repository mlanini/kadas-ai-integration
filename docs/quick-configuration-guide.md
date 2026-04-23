# Quick configuration guide for beginners

This guide helps you run the KADAS AI Integrations project with the least amount of setup.

## What you need

Before starting, make sure you have:

- KADAS Albireo installed
- Python available at `<path_to_KadasAlbireo>\bin\python.exe`
- This repository opened in VS Code

## 1. Verify the KADAS Python path

The project is configured to use:

- `<path_to_KadasAlbireo>\bin\python.exe`

You can verify it in:

- [.vscode/mcp.json](../.vscode/mcp.json)

If KADAS is installed in a different folder, update every `command` entry in that file.

## 2. Understand what is already configured

The repository already contains:

- MCP server definitions for VS Code in [.vscode/mcp.json](../.vscode/mcp.json)
- a Claude Desktop example in [examples/claude_desktop_config.json](../examples/claude_desktop_config.json)
- shared MCP runtime code in [mcp/kadas-mcp-core](../mcp/kadas-mcp-core)
- six reference MCP servers in [mcp/servers](../mcp/servers)

## 3. Available MCP servers

The following servers are already configured:

- `kadas-map`
- `kadas-geodata`
- `kadas-analysis`
- `kadas-sketching`
- `kadas-geolocation`
- `kadas-geoai`

## 4. Recommended first check

A simple beginner validation is:

- confirm that the Python executable exists
- confirm that the server modules import correctly
- confirm that each server registers its tools

This project has already been validated with the KADAS Python runtime.

## 5. Start with the most useful servers

If you are new, begin with these two:

### `kadas-map`

Use it to:

- read the current extent
- inspect layers
- center the map
- add a WMS layer reference

### `kadas-geodata`

Use it to:

- search STAC catalogs
- inspect STAC items
- discover WMS/WFS services
- download STAC assets

Together, these are enough to build a first geospatial chatbot or search assistant.

## 6. Beginner workflow

A good first workflow is:

1. read the current map extent
2. query the STAC API at `https://data.geo.admin.ch/api/stac/v0.9/`
3. show the matching items
4. zoom to the selected result
5. annotate the map

If you want a concrete example, see:

- [Mini guide for KADAS AI plugins](mini-guida-plugin-kadas-ai.md)

## 7. If you want to use Claude Desktop

Use the example file:

- [examples/claude_desktop_config.json](../examples/claude_desktop_config.json)

You will need to adjust absolute paths if your local folder is different.

## 8. If something does not work

Check these first:

- the KADAS Python path is correct
- the repository folder matches the configured `cwd` values
- required remote services are reachable
- the MCP client is reading the correct config file

## 9. Suggested next step

Once the basic setup works, the easiest next milestone is to build a small KADAS plugin with:

- a dock widget
- a text input box
- a STAC search action
- a result list
- a zoom or annotation action

That gives you a minimal but useful AI-assisted geospatial workflow.
