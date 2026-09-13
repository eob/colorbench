import type { Hsl, Oklab, Oklch, Rgb } from "./types.ts";

// Oklab matrices: https://bottosson.github.io/posts/oklab/ (2021 revision).
// Input/output RGB channels are gamma-encoded sRGB on the 0–255 scale.
export function normalizeHue(h: number): number {
  return ((h % 360) + 360) % 360;
}
export function hueDistance(a: number, b: number): number {
  const d = Math.abs(normalizeHue(a) - normalizeHue(b));
  return Math.min(d, 360 - d);
}
function linear(v: number): number {
  const n = v / 255;
  return n <= 0.04045 ? n / 12.92 : ((n + 0.055) / 1.055) ** 2.4;
}
function encoded(v: number): number {
  return 255 * (v <= 0.0031308 ? 12.92 * v : 1.055 * v ** (1 / 2.4) - 0.055);
}
export function rgbToOklab(rgb: Rgb): Oklab {
  const [r, g, b] = rgb.map(linear);
  const l = Math.cbrt(0.4122214708 * r! + 0.5363325363 * g! + 0.0514459929 * b!);
  const m = Math.cbrt(0.2119034982 * r! + 0.6806995451 * g! + 0.1073969566 * b!);
  const s = Math.cbrt(0.0883024619 * r! + 0.2817188376 * g! + 0.6299787005 * b!);
  return {
    l: 0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    a: 1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    b: 0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
  };
}
export function oklabToRgb({ l, a, b }: Oklab): Rgb {
  const x = (l + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const y = (l - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const z = (l - 0.0894841775 * a - 1.291485548 * b) ** 3;
  return [
    encoded(4.0767416621 * x - 3.3077115913 * y + 0.2309699292 * z),
    encoded(-1.2684380046 * x + 2.6097574011 * y - 0.3413193965 * z),
    encoded(-0.0041960863 * x - 0.7034186147 * y + 1.707614701 * z),
  ];
}
export function rgbToOklch(rgb: Rgb): Oklch {
  const { l, a, b } = rgbToOklab(rgb);
  const c = Math.hypot(a, b);
  return {
    l,
    c: c < 1e-7 ? 0 : c,
    h: c < 1e-7 ? 0 : normalizeHue((Math.atan2(b, a) * 180) / Math.PI),
  };
}
export function oklchToRgb({ l, c, h }: Oklch): Rgb {
  const radians = (h * Math.PI) / 180;
  return oklabToRgb({ l, a: c * Math.cos(radians), b: c * Math.sin(radians) });
}
export function rgbToHsl(rgb: Rgb): Hsl {
  const [r, g, b] = rgb.map((v) => v / 255) as Rgb;
  const max = Math.max(r, g, b),
    min = Math.min(r, g, b),
    delta = max - min;
  const l = (max + min) / 2;
  if (delta === 0) return { h: 0, s: 0, l: l * 100 };
  const hue = max === r ? (g - b) / delta : max === g ? (b - r) / delta + 2 : (r - g) / delta + 4;
  return { h: normalizeHue(hue * 60), s: (delta / (1 - Math.abs(2 * l - 1))) * 100, l: l * 100 };
}
export function hslToRgb({ h, s, l }: Hsl): Rgb {
  const light = l / 100,
    saturation = s / 100;
  const a = saturation * Math.min(light, 1 - light);
  return [0, 8, 4].map((n) => {
    const k = (n + normalizeHue(h) / 30) % 12;
    return 255 * (light - a * Math.max(-1, Math.min(k - 3, 9 - k, 1)));
  }) as Rgb;
}
export function quantizeRgb(rgb: Rgb): Rgb {
  // Only absorb matrix round-trip floating error, never visible gamut clipping.
  if (rgb.some((v) => !Number.isFinite(v) || v < -0.001 || v > 255.001))
    throw new Error("Color lies outside the sRGB gamut");
  return rgb.map((v) => Math.round(Math.max(0, Math.min(255, v)))) as Rgb;
}
export function fromOklch(l: number, c: number, h: number): Rgb {
  return quantizeRgb(oklchToRgb({ l, c, h }));
}
