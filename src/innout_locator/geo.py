from __future__ import annotations

import math

import httpx

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def km_to_mi(km: float) -> float:
    return km * 0.6213711922


def geolocate_by_ip(timeout: float = 5.0) -> tuple[float, float] | None:
    """Best-effort device location via public IP geolocation.

    Returns (lat, lon) or None.  The MCP server has no access to real
    device GPS, so this uses the outbound IP of whatever host the server
    runs on.  Callers who care about accuracy should pass explicit
    coordinates to the tool instead.
    """
    try:
        with httpx.Client(timeout=timeout) as c:
            r = c.get("https://ipinfo.io/json")
            r.raise_for_status()
            data = r.json()
            loc = data.get("loc")  # "lat,lon"
            if not loc or "," not in loc:
                return None
            lat_s, lon_s = loc.split(",", 1)
            return float(lat_s), float(lon_s)
    except Exception:
        return None
