"""Async REST client for the Aquascape Blynk backend."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

from aiohttp import ClientError, ClientSession

from .const import DEFAULT_BASE_URL, V3_DELIM

_LOGGER = logging.getLogger(__name__)


class AquascapeAPIError(Exception):
    """Raised when the Aquascape backend returns an error or is unreachable."""


class AquascapeAuthError(AquascapeAPIError):
    """Raised when the auth token is rejected."""


class AquascapeClient:
    """Thin wrapper around the Aquascape (Blynk-based) HTTPS API.

    The endpoint structure was reverse-engineered — Aquascape doesn't publish
    one. See the project README for the pin map.
    """

    def __init__(
        self,
        session: ClientSession,
        token: str,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        self._session = session
        self._token = token
        self._base_url = base_url.rstrip("/")

    async def is_connected(self) -> bool:
        """Return True if the device's hardware-side WebSocket is online.

        Used both for config-flow validation and as a liveness probe.
        """
        url = f"{self._base_url}/external/api/isHardwareConnected?token={self._token}"
        try:
            async with self._session.get(url, timeout=10) as resp:
                if resp.status == 401 or resp.status == 403:
                    raise AquascapeAuthError(f"Token rejected ({resp.status})")
                if resp.status == 404 or resp.status >= 500:
                    raise AquascapeAPIError(f"Backend error: HTTP {resp.status}")
                text = (await resp.text()).strip().lower()
                return text == "true"
        except ClientError as err:
            raise AquascapeAPIError(f"Network error: {err}") from err

    async def get_all(self) -> dict[str, Any]:
        """Fetch every populated virtual pin in a single request."""
        url = f"{self._base_url}/external/api/getAll?token={self._token}"
        try:
            async with self._session.get(url, timeout=10) as resp:
                if resp.status == 401 or resp.status == 403:
                    raise AquascapeAuthError(f"Token rejected ({resp.status})")
                if resp.status >= 400:
                    raise AquascapeAPIError(f"HTTP {resp.status}")
                return await resp.json(content_type=None)
        except ClientError as err:
            raise AquascapeAPIError(f"Network error: {err}") from err

    async def write_pin(self, pin: str, value: str | int) -> None:
        """Write a single virtual pin.

        For V3 (color/animation), pre-build the value with `\\x00` separators
        and pass it as a string — this method handles URL-encoding.
        """
        encoded = quote(str(value), safe="")
        url = (
            f"{self._base_url}/external/api/update"
            f"?token={self._token}&{pin}={encoded}"
        )
        try:
            async with self._session.get(url, timeout=10) as resp:
                if resp.status == 401 or resp.status == 403:
                    raise AquascapeAuthError(f"Token rejected ({resp.status})")
                if resp.status >= 400:
                    raise AquascapeAPIError(
                        f"Write {pin}={value} failed: HTTP {resp.status}"
                    )
        except ClientError as err:
            raise AquascapeAPIError(f"Network error: {err}") from err


def build_solid_v3(r: int, g: int, b: int) -> str:
    """Build a V3 string for a solid RGB color (RGB-channel mode on)."""
    return f"{r}{V3_DELIM}{g}{V3_DELIM}{b}{V3_DELIM}true"


def build_white_mode_v3() -> str:
    """V3 value that switches to the dedicated white channel."""
    return f"255{V3_DELIM}255{V3_DELIM}255{V3_DELIM}false"


def build_animation_v3(
    palette: list[tuple[int, int, int]],
    *,
    strobe: bool,
) -> str:
    """Build a V3 animation string from a palette of RGB triplets.

    Format: <currR>\\x00<currG>\\x00<currB>\\x00true\\x00<strobe>\\x00<R\\x00G\\x00B...>
    `current` is set to the first palette entry — the device updates the
    displayed color as it cycles.
    """
    if not palette:
        raise ValueError("palette must contain at least one color")
    first = palette[0]
    strobe_flag = "1" if strobe else "0"
    parts: list[str] = [
        str(first[0]),
        str(first[1]),
        str(first[2]),
        "true",
        strobe_flag,
    ]
    for r, g, b in palette:
        parts.extend([str(r), str(g), str(b)])
    return V3_DELIM.join(parts)


def parse_v3(v3: str) -> dict[str, Any]:
    """Decode a V3 string into structured fields.

    Returns a dict with keys:
        rgb: (r, g, b) — current displayed color
        rgb_mode: bool — RGB channels (True) vs white channel (False)
        strobe: bool | None — None if not in animation mode
        palette: list[(r,g,b)] — empty if solid
    """
    parts = v3.split(V3_DELIM)
    if len(parts) < 4:
        return {"rgb": (0, 0, 0), "rgb_mode": False, "strobe": None, "palette": []}

    def safe_int(s: str, default: int = 0) -> int:
        try:
            return int(s)
        except (ValueError, TypeError):
            return default

    rgb = (safe_int(parts[0]), safe_int(parts[1]), safe_int(parts[2]))
    rgb_mode = parts[3].lower() == "true"

    if len(parts) <= 4:
        # solid (no strobe flag, no palette)
        return {"rgb": rgb, "rgb_mode": rgb_mode, "strobe": None, "palette": []}

    strobe = parts[4] == "1"
    palette_raw = parts[5:]
    palette: list[tuple[int, int, int]] = []
    for i in range(0, len(palette_raw) - 2, 3):
        palette.append(
            (
                safe_int(palette_raw[i]),
                safe_int(palette_raw[i + 1]),
                safe_int(palette_raw[i + 2]),
            )
        )
    return {"rgb": rgb, "rgb_mode": rgb_mode, "strobe": strobe, "palette": palette}
