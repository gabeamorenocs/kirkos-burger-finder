# innout-locator-mcp

An MCP (Model Context Protocol) server that lists In-N-Out Burger
locations in a given US state, sorted nearest-first relative to the
device calling the tool.

> In-N-Out Burger operates only in the United States, so the
> "worldwide" universe of franchise locations is the US set. The
> server will happily accept any of the 50 states + DC; states where
> In-N-Out has no presence simply return `count: 0`.

## Data source

Locations are pulled live from **OpenStreetMap** via the public
[Overpass API](https://overpass-api.de/), querying for
`brand="In-N-Out Burger"` inside the requested state's `ISO3166-2`
boundary. OSM's coverage of In-N-Out is effectively complete, and the
Overpass API needs no auth and is kinder than scraping in-n-out.com.

The server falls back across three Overpass mirrors if one is down.

## Tools exposed

### `find_in_n_out_by_state(state, user_lat?, user_lon?, units?)`

Returns every In-N-Out in the given state, sorted by distance from the
caller.

| arg          | type   | notes                                                            |
| ------------ | ------ | ---------------------------------------------------------------- |
| `state`      | string | `"CA"` or `"California"` — any US state code or name.            |
| `user_lat`   | float  | Optional. Latitude of the device making the request.             |
| `user_lon`   | float  | Optional. Longitude of the device making the request.            |
| `units`      | string | `"mi"` (default) or `"km"` — picks the summary unit; both are returned per-row. |

Origin resolution, in order:

1. Explicit `user_lat` / `user_lon` arguments (always preferred).
2. `INNOUT_USER_LAT` / `INNOUT_USER_LON` environment variables.
3. IP-based geolocation of the host running the server (city-level
   accuracy at best — the server has no access to real device GPS).

If none of those produce an origin, results are returned in a stable
alphabetical order instead of by distance and `origin` is `null`.

### `list_supported_states()`

Returns every US state code/name the server will accept.

## Install & run

```bash
pip install -e .
innout-locator-mcp
```

The server speaks MCP over stdio.

## Wire it into Claude Code

Add to `~/.claude/mcp.json` (or project `.mcp.json`):

```json
{
  "mcpServers": {
    "innout": {
      "command": "innout-locator-mcp"
    }
  }
}
```

Then in a Claude Code session:

> *list every In-N-Out in Nevada, nearest to me first*

## Caveats

- **Device location.** MCP servers run wherever the host puts them,
  not on the user's phone, so "proximity to the device" is only as
  good as the origin the server can resolve. For real device GPS,
  pass `user_lat` / `user_lon` explicitly from a client that has it.
- **OSM freshness.** New In-N-Out openings land in OSM within days
  typically but not instantly. For an authoritative list, hit
  in-n-out.com directly.
