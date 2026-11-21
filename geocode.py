"""Reverse geocoding for the GPS location hint."""

from functools import lru_cache

import requests

_URL = "https://nominatim.openstreetmap.org/reverse"


@lru_cache(maxsize=64)
def _lookup(lat: float, lon: float) -> tuple[str, str]:
    try:
        response = requests.get(
            _URL,
            params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 13},
            headers={"User-Agent": "CroporaAI/1.0 (student project)"},
            timeout=6,
        )
        data = response.json()
    except (requests.RequestException, ValueError):
        return "", ""
    address = data.get("address") or {}
    place = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("suburb")
        or address.get("county")
        or ""
    )
    state = address.get("state") or ""
    pin = address.get("postcode") or ""
    label = ", ".join(part for part in (place, state) if part)
    return label, pin


def reverse_location(lat: float, lon: float) -> str:
    """A short 'City, State · PIN 000000' label, or '' when unavailable."""
    label, pin = _lookup(round(lat, 3), round(lon, 3))
    parts = [label] if label else []
    if pin:
        parts.append(f"PIN {pin}")
    return "GPS: " + " · ".join(parts) if parts else ""
