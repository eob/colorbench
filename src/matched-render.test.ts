import { expect, test } from "bun:test";
import { chromium } from "playwright";
import { PROMPTS } from "./prompts.ts";
import { generateHtml, placeFields, VIEWPORT } from "./render.ts";
import type { ColorSpecimenConfig, Rgb } from "./types.ts";

const sample: ColorSpecimenConfig = {
  taskId: "control", family: "smallmatch", groupId: "paired", imageId: "control",
  target: { rgb: [80, 120, 150] },
  options: [[80, 120, 150], [90, 120, 150], [100, 120, 150], [110, 120, 150]].map(
    (rgb) => ({ rgb: rgb as Rgb }),
  ),
  answer: "A",
  design: { axis: "lightness", difficulty: "mid", layout: "dot", sizePx: 20, strokePx: 0 },
};

test("outline and neutral-surround instructions describe all matched conditions", () => {
  expect(PROMPTS.smallmatch).toContain("including colored outlines");
  expect(PROMPTS.smallmatch).not.toContain("not labels or borders");
  expect(PROMPTS.context).not.toContain("Each option sits on a different surround");
});

test("filled-size conditions retain field centers and label positions", () => {
  const large = { ...sample, design: { ...sample.design, sizePx: 84 } };
  const smallFields = placeFields(sample);
  const largeFields = placeFields(large);
  expect(largeFields.map((r) => r.width)).toEqual([84, 84, 84, 84, 84]);
  expect(smallFields.map((r) => [r.x + r.width / 2, r.y + r.height / 2])).toEqual(
    largeFields.map((r) => [r.x + r.width / 2, r.y + r.height / 2]),
  );
  const labels = (s: ColorSpecimenConfig) => generateHtml(s).match(/<div class="label"[^>]+>/g);
  expect(labels(sample)).toEqual(labels(large));
});

test("outline width changes only the colored stroke at fixed outer dimensions", async () => {
  const frame = (strokePx: number): ColorSpecimenConfig => ({
    ...sample, design: { ...sample.design, layout: "frame", sizePx: 84, strokePx },
  });
  expect(placeFields(frame(12)).every((r) => r.width === 84 && r.ring?.width === 12)).toBe(true);
  const browser = await chromium.launch({ args: ["--force-color-profile=srgb"] });
  try {
    const page = await browser.newPage({ viewport: VIEWPORT });
    const probes: number[][] = [];
    for (const width of [3, 12]) {
      await page.setContent(generateHtml(frame(width)));
      probes.push(await page.evaluate(() => Array.from(
        document.querySelector<HTMLCanvasElement>('canvas[data-region="R"]')!
          .getContext("2d")!.getImageData(6, 42, 1, 1).data,
      )));
    }
    expect(probes).toEqual([[238, 238, 238, 255], [80, 120, 150, 255]]);
  } finally {
    await browser.close();
  }
});

test("context renders recorded neutral and rotated surrounds", () => {
  const surround = { A: [238, 238, 238], B: [238, 238, 238], C: [238, 238, 238], D: [238, 238, 238] };
  const s: ColorSpecimenConfig = { ...sample, family: "context", design: {
    axis: "lightness", difficulty: "mid", surround,
  } };
  expect(placeFields(s).filter((r) => r.role === "option").map((r) => r.ring?.color)).toEqual(
    Object.values(surround),
  );
  const rotated = { A: [1, 2, 3], B: [4, 5, 6], C: [7, 8, 9], D: [10, 11, 12] };
  expect(placeFields({ ...s, design: { ...s.design, surround: rotated } })
    .filter((r) => r.role === "option").map((r) => r.ring?.color)).toEqual(Object.values(rotated));
});
