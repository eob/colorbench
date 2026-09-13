import { describe, expect, test } from "bun:test";
import {
  rgbToOklab,
  oklabToRgb,
  rgbToOklch,
  oklchToRgb,
  rgbToHsl,
  hslToRgb,
  quantizeRgb,
  hueDistance,
} from "./colors.ts";

describe("frozen color conversions", () => {
  test("matches independently published sRGB primary Oklab values", () => {
    const red = rgbToOklab([255, 0, 0]);
    expect(red.l).toBeCloseTo(0.62795536, 7);
    expect(red.a).toBeCloseTo(0.22486306, 7);
    expect(red.b).toBeCloseTo(0.1258463, 7);
    const blue = rgbToOklab([0, 0, 255]);
    expect(blue.l).toBeCloseTo(0.45201372, 7);
    expect(blue.a).toBeCloseTo(-0.03245698, 7);
    expect(blue.b).toBeCloseTo(-0.31152815, 7);
  });
  test("uses explicit HSL units and canonical achromatic hue", () => {
    expect(rgbToHsl([255, 0, 0])).toEqual({ h: 0, s: 100, l: 50 });
    expect(rgbToHsl([0, 255, 0])).toEqual({ h: 120, s: 100, l: 50 });
    expect(rgbToHsl([128, 128, 128]).h).toBe(0);
    expect(rgbToOklch([128, 128, 128]).h).toBe(0);
    expect(hueDistance(359, 1)).toBe(2);
    expect(quantizeRgb(hslToRgb({ h: 360, s: 100, l: 50 }))).toEqual([255, 0, 0]);
  });
  test("round trips a grid including neutrals and gamut boundaries", () => {
    for (const r of [0, 17, 128, 239, 255])
      for (const g of [0, 64, 128, 255])
        for (const b of [0, 1, 128, 254, 255]) {
          const rgb: [number, number, number] = [r, g, b];
          expect(quantizeRgb(oklabToRgb(rgbToOklab(rgb)))).toEqual(rgb);
          expect(quantizeRgb(oklchToRgb(rgbToOklch(rgb)))).toEqual(rgb);
          expect(quantizeRgb(hslToRgb(rgbToHsl(rgb)))).toEqual(rgb);
        }
  });
  test("rejects out-of-gamut construction instead of silently clipping", () => {
    expect(() => quantizeRgb(oklchToRgb({ l: 0.65, c: 0.5, h: 40 }))).toThrow("gamut");
    expect(() => quantizeRgb([Number.NaN, 0, 0])).toThrow();
  });
});
