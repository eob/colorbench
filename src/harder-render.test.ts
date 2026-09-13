import { describe, expect, test } from "bun:test";
import * as fs from "node:fs";
import * as path from "node:path";
import { chromium } from "playwright";
import { PROMPTS, getPrompt } from "./prompts.ts";
import { generateHtml, groundTruthFromPixels, placeFields, VIEWPORT } from "./render.ts";
import { SPECIMENS } from "./specimens.ts";
import type { ColorSpecimenConfig, PixelRegion } from "./types.ts";

const region = (role: PixelRegion["role"], id: string, sha: string, rgb?: [number, number, number]) =>
  ({
    role,
    id,
    x: 0,
    y: 0,
    width: 8,
    height: 8,
    ...(rgb ? { rgb } : {}),
    pixelSha256: sha,
  }) as PixelRegion;

describe("harder family rendering", () => {
  test("typescript prompts match the python protocol bytes exactly", () => {
    const frozen = JSON.parse(
      fs.readFileSync(path.join(import.meta.dir, "../baseline/prompts.json"), "utf8"),
    );
    expect(PROMPTS).toEqual(frozen);
    expect(getPrompt({ family: "samediff", design: { direction: "sameB" } } as ColorSpecimenConfig)).toBe(
      frozen["samediff-sameB"],
    );
  });
  test("samediff places two patches with no target and keeps images mapping-neutral", () => {
    for (const direction of ["sameA", "sameB"]) {
      const specimen = {
        taskId: "t",
        family: "samediff",
        groupId: "g",
        imageId: "i",
        options: [{ rgb: [1, 2, 3] }, { rgb: [1, 2, 3] }],
        answer: "A",
        design: { axis: "identity", difficulty: "same", direction, same: true, intendedSeparation: 0 },
      } as ColorSpecimenConfig;
      const fields = placeFields(specimen);
      expect(fields.filter((f) => f.role === "target")).toHaveLength(0);
      expect(fields.filter((f) => f.role === "option")).toHaveLength(2);
      const html = generateHtml(specimen);
      expect(html).toContain("Are A and B the same color?");
      expect(html).not.toContain("for same");
      expect(html).not.toContain("for different");
    }
  });
  test("samediff ground truth derives choice from equality and mapping", () => {
    const specimen = (answer: string, direction: string, same: boolean) =>
      ({
        taskId: "t",
        family: "samediff",
        design: { axis: "identity", difficulty: "same", direction, same, intendedSeparation: 0 },
        answer,
      }) as unknown as ColorSpecimenConfig;
    const sameRegions = [region("option", "A", "aa"), region("option", "B", "aa")];
    expect(groundTruthFromPixels(specimen("A", "sameA", true), sameRegions)).toEqual({ choice: "A" });
    expect(groundTruthFromPixels(specimen("B", "sameB", true), sameRegions)).toEqual({ choice: "B" });
    const diffRegions = [region("option", "A", "aa"), region("option", "B", "bb")];
    expect(groundTruthFromPixels(specimen("B", "sameA", false), diffRegions)).toEqual({ choice: "B" });
    expect(groundTruthFromPixels(specimen("A", "sameB", false), diffRegions)).toEqual({ choice: "A" });
    expect(() => groundTruthFromPixels(specimen("B", "sameA", true), sameRegions)).toThrow(
      "Decoded ground truth differs",
    );
  });
  test("context records interior regions inside fixed surround canvases", () => {
    const specimen = {
      taskId: "t",
      family: "context",
      groupId: "g",
      imageId: "i",
      target: { rgb: [10, 20, 30] },
      options: [{ rgb: [10, 20, 30] }, { rgb: [11, 20, 30] }, { rgb: [12, 20, 30] }, { rgb: [13, 20, 30] }],
      answer: "A",
      design: { axis: "test", difficulty: "mid" },
    } as unknown as ColorSpecimenConfig;
    const fields = placeFields(specimen);
    const options = fields.filter((f) => f.role === "option");
    expect(options).toHaveLength(4);
    for (const option of options) {
      expect([option.width, option.height]).toEqual([84, 84]);
      expect([option.canvasWidth, option.canvasHeight]).toEqual([108, 108]);
      expect(option.ring?.width).toBe(12);
    }
    const rings = options.map((o) => JSON.stringify(o.ring?.color));
    expect(new Set(rings).size).toBe(4);
    const target = fields.find((f) => f.role === "target")!;
    expect([target.width, target.height]).toEqual([84, 84]);
    const regions = [
      region("target", "R", "rr", [10, 20, 30]),
      region("option", "A", "rr", [10, 20, 30]),
      region("option", "B", "b1", [11, 20, 30]),
      region("option", "C", "c1", [12, 20, 30]),
      region("option", "D", "d1", [13, 20, 30]),
    ];
    expect(groundTruthFromPixels(specimen, regions)).toEqual({ choice: "A" });
  });
  test("smallmatch dot uses 20px fields and frame uses outlined fields", () => {
    const dot = {
      taskId: "t",
      family: "smallmatch",
      groupId: "g",
      imageId: "i",
      target: { rgb: [10, 20, 30] },
      options: [{ rgb: [10, 20, 30] }, { rgb: [11, 20, 30] }, { rgb: [12, 20, 30] }, { rgb: [13, 20, 30] }],
      answer: "A",
      design: { axis: "test", difficulty: "mid", layout: "dot" },
    } as unknown as ColorSpecimenConfig;
    for (const field of placeFields(dot)) expect([field.width, field.height]).toEqual([20, 20]);
    expect(generateHtml(dot)).toContain("colored interiors");
    const frame = {
      ...dot,
      design: { axis: "test", difficulty: "mid", layout: "frame" },
    } as unknown as ColorSpecimenConfig;
    const frameFields = placeFields(frame);
    for (const field of frameFields) {
      expect([field.width, field.height]).toEqual([84, 84]);
      expect(field.ring?.width).toBe(3);
    }
    const html = generateHtml(frame);
    expect(html).toContain("238,238,238");
    expect(html).toContain("colored outlines");
  });
  test("frame canvases paint ring color on the border and background inside", async () => {
    const specimen = SPECIMENS.find(
      (s) => s.family === "smallmatch" && s.design.layout === "frame",
    )!;
    const browser = await chromium.launch({ args: ["--force-color-profile=srgb"] });
    try {
      const page = await browser.newPage({
        viewport: { width: VIEWPORT.width, height: VIEWPORT.height },
        deviceScaleFactor: 1,
      });
      await page.setContent(generateHtml(specimen));
      await page.evaluate(() => document.fonts.ready);
      const pixels = await page.evaluate(() => {
        const canvas = document.querySelector<HTMLCanvasElement>('canvas[data-region="R"]')!;
        const ctx = canvas.getContext("2d")!;
        const at = (x: number, y: number) => Array.from(ctx.getImageData(x, y, 1, 1).data);
        return { border: at(1, 1), middle: at(42, 42) };
      });
      expect(pixels.border.slice(0, 3)).toEqual(specimen.target!.rgb!);
      expect(pixels.middle).toEqual([238, 238, 238, 255]);
    } finally {
      await browser.close();
    }
  });
});
