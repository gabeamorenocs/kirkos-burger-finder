"""MCP server exposing In-N-Out Burger locations by state, sorted by distance.

Tools:
  * find_in_n_out_by_state(state, user_lat?, user_lon?, units?)
        List every In-N-Out in the given state, nearest first.

  * list_supported_states()
        Return the 50 US state codes/names (In-N-Out operates only in
        the US; the "worldwide" universe is the US).
"""
from __future__ import annotations

import os
from typing import Any

from mcp.server.mcpserver import MCPServer

from .geo import geolocate_by_ip, haversine_km, km_to_mi
from .locations import Restaurant, fetch_locations
from .states import US_STATES, resolve_state

mcp = MCPServer("innout-locator")


def _resolve_origin(
    user_lat: float | None,
    user_lon: float | None,
) -> tuple[tuple[float, float] | None, str]:
    """Pick the origin point and label its source."""
    if user_lat is not None and user_lon is not None:
        return (user_lat, user_lon), "user-supplied coordinates"
    env_lat = os.environ.get("INNOUT_USER_LAT")
    env_lon = os.environ.get("INNOUT_USER_LON")
    if env_lat and env_lon:
        try:
            return (float(env_lat), float(env_lon)), "INNOUT_USER_LAT/LON env vars"
        except ValueError:
            pass
    ip = geolocate_by_ip()
    if ip is not None:
        return ip, "IP geolocation (approximate — city-level)"
    return None, "no origin available"


def _format_row(r: Restaurant, origin: tuple[float, float] | None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "name": r.name,
        "address": r.address or None,
        "lat": r.lat,
        "lon": r.lon,
        "osm_id": r.osm_id,
    }
    if origin is not None:
        km = haversine_km(origin[0], origin[1], r.lat, r.lon)
        row["distance_km"] = round(km, 2)
        row["distance_mi"] = round(km_to_mi(km), 2)
    return row


@mcp.tool()
def list_supported_states() -> dict[str, Any]:
    """List every US state In-N-Out might operate in (the whole US set).

    In-N-Out Burger is a US-only chain, so the "worldwide" universe
    reduces to US states.  Any of these codes or names is accepted by
    `find_in_n_out_by_state`.
    """
    return {"states": [{"code": c, "name": n} for c, n in sorted(US_STATES.items())]}


@mcp.tool()
def find_in_n_out_by_state(
    state: str,
    user_lat: float | None = None,
    user_lon: float | None = None,
    units: str = "mi",
) -> dict[str, Any]:
    """Return every In-N-Out in `state`, sorted nearest-first.

    Args:
      state:      Two-letter code ("CA") or full name ("California").
      user_lat:   Optional latitude of the device requesting the list.
      user_lon:   Optional longitude of the device requesting the list.
                  If either coordinate is omitted the server falls back
                  to the INNOUT_USER_LAT/LON env vars, then to IP-based
                  geolocation of the host running the MCP server.
      units:      "mi" (default) or "km" — purely controls which field
                  is used for the human-readable summary; both are
                  always included on every row.

    Returns:
      {
        "state":   { "code": "CA", "name": "California" },
        "origin":  { "lat": .., "lon": .., "source": "..." } | None,
        "count":   <int>,
        "results": [ { name, address, lat, lon, distance_km, distance_mi, osm_id }, ... ]
      }
    """
    resolved = resolve_state(state)
    if resolved is None:
        return {
            "error": f"Unknown US state: {state!r}. Call list_supported_states for valid values.",
        }
    code, name = resolved

    origin, origin_source = _resolve_origin(user_lat, user_lon)

    try:
        restaurants = fetch_locations(code)
    except Exception as exc:
        return {"error": f"Could not fetch locations: {exc}"}

    if origin is not None:
        restaurants.sort(key=lambda r: haversine_km(origin[0], origin[1], r.lat, r.lon))
    else:
        restaurants.sort(key=lambda r: (r.city or "", r.street or ""))

    rows = [_format_row(r, origin) for r in restaurants]

    unit_key = "distance_mi" if units.lower() == "mi" else "distance_km"
    unit_label = "mi" if units.lower() == "mi" else "km"

    return {
        "state": {"code": code, "name": name},
        "origin": (
            {"lat": origin[0], "lon": origin[1], "source": origin_source}
            if origin is not None
            else None
        ),
        "count": len(rows),
        "units": unit_label,
        "distance_field": unit_key,
        "results": rows,
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
