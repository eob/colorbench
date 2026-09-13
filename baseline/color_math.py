"""sRGB/D65 conversions; no gamut clipping or perceptual-threshold claims.

Oklab matrices: Björn Ottosson's public-domain 2021-01-25 implementation,
https://bottosson.github.io/posts/oklab/#converting-from-linear-srgb-to-oklab.
HSL follows CSS Color 4. Input validation belongs to the prediction schema.
"""

from __future__ import annotations

import colorsys
import math
from collections.abc import Sequence


def _linear(channel: float) -> float:
    normalized = channel / 255.0
    magnitude = abs(normalized)
    value = magnitude / 12.92 if magnitude <= 0.04045 else ((magnitude + 0.055) / 1.055) ** 2.4
    return math.copysign(value, normalized)


def rgb_to_oklab(rgb: Sequence[float]) -> tuple[float, float, float]:
    r, g, b = map(_linear, rgb)
    cone = (
        0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b,
        0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b,
        0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b,
    )
    l, m, s = (math.copysign(abs(v) ** (1 / 3), v) for v in cone)
    return (
        0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
        1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
        0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
    )


def rgb_to_hsl(rgb: Sequence[float]) -> dict[str, float]:
    h, l, s = colorsys.rgb_to_hls(*(v / 255.0 for v in rgb))
    return {"h": h * 360.0, "s": s * 100.0, "l": l * 100.0}


def hsl_to_rgb(h: float, s: float, l: float) -> tuple[float, float, float]:
    return tuple(v * 255.0 for v in colorsys.hls_to_rgb((h % 360) / 360, l / 100, s / 100))


def rgb_to_oklch(rgb: Sequence[float]) -> dict[str, float]:
    l, a, b = rgb_to_oklab(rgb)
    if rgb[0] == rgb[1] == rgb[2]:
        return {"l": l, "c": 0.0, "h": 0.0}
    return {"l": l, "c": math.hypot(a, b), "h": math.degrees(math.atan2(b, a)) % 360}


def oklch_to_oklab(l: float, c: float, h: float) -> tuple[float, float, float]:
    radians = math.radians(h % 360)
    return l, c * math.cos(radians), c * math.sin(radians)


def oklab_to_linear_rgb(lab: Sequence[float]) -> tuple[float, float, float]:
    lightness, a, b = lab
    l = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )
