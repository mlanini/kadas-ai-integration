# Quick Starter: building KADAS plugins that use AI integrations

This guide shows how to set up a KADAS plugin that uses the framework in this repository to build geospatial AI features, for example a chatbot that searches and visualizes data from the `data.geo.admin.ch` STAC API.

## Goal

Build a KADAS plugin that lets a user write requests such as:

- "Show me STAC datasets related to snow in the Swiss Alps"
- "Search for recent imagery in the Bern area"
- "Display the available layers for this area"

The plugin should:

1. collect the current map context;
2. query the STAC API at `https://data.geo.admin.ch/api/stac/v0.9/`;
3. present the results in a simple UI;
4. add or annotate relevant data on the map.

## Recommended architecture

For a lightweight KADAS plugin, use this separation:

- **KADAS plugin**: UI, dock panel, user input handling, PyQGIS/KADAS interaction;
- **MCP servers**: reusable geospatial logic;
- **LLM/chat layer**: translation from natural language into tool calls.

### Most useful framework tools

- `kadas-map`
  - `get_extent`
  - `fly_to`
  - `add_wms_layer`
  - `list_layers`
- `kadas-geodata`
  - `search_stac_catalog`
  - `get_stac_item`
  - `download_stac_asset`
  - `discover_wms`
- `kadas-sketching`
  - `add_pin`
  - `add_text`

## Reference STAC API

The geo.admin.ch STAC API exposes at least these useful endpoints:

- landing page: `https://data.geo.admin.ch/api/stac/v0.9/`
- collections: `https://data.geo.admin.ch/api/stac/v0.9/collections`
- search GET/POST: `https://data.geo.admin.ch/api/stac/v0.9/search`
- browser: `https://data.geo.admin.ch/browser/index.html#/`

## Minimal plugin structure

A simple starting structure can be:

```text
my_kadas_ai_chatbot/
├── __init__.py
├── metadata.txt
├── main_plugin.py
├── ui/
│   └── chatbot_panel.py
├── services/
│   ├── mcp_client.py
│   ├── stac_service.py
│   └── llm_service.py
└── resources/
```

## Recommended chatbot flow

### 1. Read the map context

Before querying data, the plugin should read:

- current extent;
- current CRS;
- active layers;
- optional user selection.

In the current framework this can be done with `kadas-map/get_extent` and `kadas-map/list_layers`.

### 2. Build a context-aware STAC query

Example:

- use the current bbox as the search filter;
- optionally add a temporal interval;
- limit the number of results;
- filter by collection when available.

Example payload for `search_stac_catalog`:

```json
{
  "api_url": "https://data.geo.admin.ch/api/stac/v0.9/",
  "bbox": [7.43, 46.93, 7.52, 47.01],
  "limit": 10
}
```

### 3. Show the results in the plugin panel

Each result should expose at least:

- `id`
- `collection`
- `datetime`
- available assets
- bbox

Suggested UI:

- chat input at the top;
- results list in the center;
- quick actions on the right or in a context menu:
  - "Zoom"
  - "Open asset"
  - "Download"
  - "Add note"

### 4. Visualize or annotate the selected result

Once an item is selected:

- use `fly_to` to center the map;
- use `add_text` or `add_pin` to mark the dataset;
- if the item or service exposes WMS resources, use `add_wms_layer`.

## Example chatbot behavior

### User prompt

> Search for recent STAC data around Zurich and show me the most relevant results.

### Internal flow

1. the plugin reads extent/CRS;
2. the LLM translates the request into a `search_stac_catalog` call;
3. the plugin shows the results;
4. when the user clicks an item:
   - call `get_stac_item`;
   - center the map;
   - annotate the result.

## Example plugin-side orchestration

Python pseudo-flow:

```python
extent = mcp.call("kadas-map", "get_extent", {})
results = mcp.call(
    "kadas-geodata",
    "search_stac_catalog",
    {
        "api_url": "https://data.geo.admin.ch/api/stac/v0.9/",
        "bbox": extent["extent"],
        "limit": 10,
    },
)
```

Then, when the user selects an item:

```python
item = mcp.call(
    "kadas-geodata",
    "get_stac_item",
    {
        "api_url": "https://data.geo.admin.ch/api/stac/v0.9/",
        "collection_id": selected_collection,
        "item_id": selected_item,
    },
)
```

## Practical pattern for `stac_service.py`

Inside the plugin, it is useful to isolate STAC logic in a dedicated class:

```python
class StacService:
    API_URL = "https://data.geo.admin.ch/api/stac/v0.9/"

    def __init__(self, mcp_client):
        self.mcp = mcp_client

    def search_in_current_extent(self, bbox, limit=10):
        return self.mcp.call(
            "kadas-geodata",
            "search_stac_catalog",
            {
                "api_url": self.API_URL,
                "bbox": bbox,
                "limit": limit,
            },
        )
```

## When to use an LLM and when not to

Use an LLM for:

- interpreting ambiguous natural-language requests;
- selecting sensible STAC filters;
- summarizing results;
- suggesting the most appropriate dataset.

Do not use an LLM for:

- reading extent/CRS;
- running deterministic STAC queries;
- adding layers or annotations;
- downloading files.

In short: **LLM for reasoning, MCP tools for execution**.

## Quality rules for KADAS AI plugins

- Always pass `bbox` and `crs` when possible.
- Limit the number of results (`limit`) to reduce noise.
- Always show the data source (`collection`, `item id`, API URL).
- Provide clear fallbacks if the STAC API does not respond.
- Keep every automated map action traceable.

## Recommended MVP

For a first version of the chatbot plugin:

1. dock widget with text input;
2. "Use current extent" button;
3. STAC search via `search_stac_catalog`;
4. results list;
5. "Zoom to item" action;
6. "Annotate result" action.

This is enough to validate the plugin + MCP + STAC pattern.

## Useful evolutions

After the MVP you can add:

- semantic ranking of results using the Rust crate in [compute/](../compute/);
- automatic collection suggestions;
- support for asset download and preview;
- change detection or segmentation tools on downloaded rasters;
- conversational memory scoped to the current map session.

## Repository files to reuse

The main references for plugin development are:

- [mcp/README.md](../mcp/README.md)
- [skills/kadas-geospatial/SKILL.md](../skills/kadas-geospatial/SKILL.md)
- [.vscode/mcp.json](../.vscode/mcp.json)
- [examples/claude_desktop_config.json](../examples/claude_desktop_config.json)

## Conclusion

The simplest way to generate AI-enabled KADAS plugins is to use the plugin as the local UI/orchestration layer and delegate reusable geospatial logic to the MCP servers in this repository.

For a STAC chatbot on `data.geo.admin.ch`, the minimal path is:

- read the map context;
- search the STAC API using the current bbox;
- show the results;
- center and annotate the selected datasets.
