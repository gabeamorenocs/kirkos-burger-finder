"""Fetch In-N-Out Burger restaurant locations from OpenStreetMap via Overpass.

Overpass is used instead of scraping in-n-out.com because it is a stable,
public, documented API with no rate-limit auth required and it carries
the brand tag (brand=In-N-Out Burger) on every store node.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

BRAND = "In-N-Out Burger"
USER_AGENT = "innout-locator-mcp/0.1 (+https://example.invalid)"


@dataclass(frozen=True)
class Restaurant:
    osm_id: str
    name: str
    lat: float
    lon: float
    street: str | None
    city: str | None
    state: str | None
    postcode: str | None

    @property
    def address(self) -> str:
        parts = [self.street, self.city, self.state, self.postcode]
        return ", ".join(p for p in parts if p)


def _build_query(state_code: str | None) -> str:
    # ISO3166-2 for US states is "US-CA" etc.
    if state_code:
        return f"""
        [out:json][timeout:60];
        area["ISO3166-2"="US-{state_code}"]->.a;
        (
          nwr["brand"="{BRAND}"](area.a);
          nwr["name"="{BRAND}"](area.a);
        );
        out center tags;
        """
    return f"""
    [out:json][timeout:90];
    (
      nwr["brand"="{BRAND}"];
      nwr["name"="{BRAND}"];
    );
    out center tags;
    """


def _parse_element(el: dict[str, Any]) -> Restaurant | None:
    tags = el.get("tags") or {}
    if el.get("type") == "node":
        lat, lon = el.get("lat"), el.get("lon")
    else:
        center = el.get("center") or {}
        lat, lon = center.get("lat"), center.get("lon")
    if lat is None or lon is None:
        return None
    return Restaurant(
        osm_id=f"{el.get('type')}/{el.get('id')}",
        name=tags.get("name") or BRAND,
        lat=float(lat),
        lon=float(lon),
        street=tags.get("addr:street"),
        city=tags.get("addr:city"),
        state=tags.get("addr:state"),
        postcode=tags.get("addr:postcode"),
    )


def fetch_locations(state_code: str | None, *, timeout: float = 90.0) -> list[Restaurant]:
    query = _build_query(state_code)
    last_err: Exception | None = None
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            with httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT}) as client:
                r = client.post(endpoint, data={"data": query})
                r.raise_for_status()
                data = r.json()
            out: list[Restaurant] = []
            seen: set[str] = set()
            for el in data.get("elements", []):
                rest = _parse_element(el)
                if rest and rest.osm_id not in seen:
                    seen.add(rest.osm_id)
                    out.append(rest)
            return out
        except Exception as exc:  # try next mirror
            last_err = exc
            time.sleep(0.5)
            continue
    raise RuntimeError(f"All Overpass endpoints failed; last error: {last_err}")
