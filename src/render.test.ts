import { describe, expect, test } from "bun:test";
import { chromium } from "playwright";
import { SPECIMENS } from "./specimens.ts";
import {
  generateHtml,
  groundTruthFromPixels,
  inspectPixels,
  placeFields,
  sha256,
  VIEWPORT,
} from "./render.ts";

describe("actual rendered evidence", () => {
  test("repeated page renders paint fresh opaque fields and reject a corrupted target", async () => {
    const browser = await chromium.launch({ args: ["--force-color-profile=srgb"] });
    try {
      const page = await browser.newPage({
        viewport: { width: VIEWPORT.width, height: VIEWPORT.height },
        deviceScaleFactor: 1,
      });
      for (const specimen of SPECIMENS.slice(0, 2)) {
        await page.setContent(generateHtml(specimen));
        await page.evaluate(() => document.fonts.ready);
        const regions = await inspectPixels(page, await page.screenshot(), placeFields(specimen));
        expect(groundTruthFromPixels(specimen, regions)).toEqual({ choice: specimen.answer! });
      }
      const specimen = SPECIMENS[1]!;
      await page.evaluate(() => {
        const ctx = document.querySelector("canvas")!.getContext("2d")!;
        ctx.fillStyle = "black";
        ctx.fillRect(0, 0, 1, 1);
      });
      await expect(
        inspectPixels(page, await page.screenshot(), placeFields(specimen)),
      ).rejects.toThrow("Decoded flat pixels");
    } finally {
      await browser.close();
    }
  });
  test("numeric image bytes do not reveal the requested representation", async () => {
    const browser = await chromium.launch({ args: ["--force-color-profile=srgb"] });
    try {
      const page = await browser.newPage({
        viewport: { width: 800, height: 640 },
        deviceScaleFactor: 1,
      });
      const hashes: string[] = [];
      for (const specimen of SPECIMENS.filter((s) => s.groupId === "numeric-01")) {
        await page.setContent(generateHtml(specimen));
        await page.evaluate(() => document.fonts.ready);
        const png = await page.screenshot();
        hashes.push(sha256(png));
        expect(
          groundTruthFromPixels(specimen, await inspectPixels(page, png, placeFields(specimen))),
        ).toEqual({ rgb: [192, 64, 80] });
      }
      expect(new Set(hashes).size).toBe(1);
    } finally {
      await browser.close();
    }
  });
});
