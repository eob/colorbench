import { describe, expect, test } from "bun:test";
import { rgbToOklch } from "./colors.ts";
import { getPrompt } from "./prompts.ts";
import { CONTEXT_SURROUNDS, GRADIENT_WIDTH, SPECIMENS } from "./specimens.ts";
import type { ColorSpecimenConfig } from "./types.ts";

function grouped(rows: ColorSpecimenConfig[], key: (row: ColorSpecimenConfig) => unknown) {
  const groups = new Map<string, ColorSpecimenConfig[]>();
  for (const row of rows) {
    const value = JSON.stringify(key(row));
    groups.set(value, [...(groups.get(value) ?? []), row]);
  }
  return [...groups.values()];
}

// This construction check uses quantized stimulus colors. The Python release
// gate separately checks the entire decoded PNG with the other patch masked.
function singlePatchCeiling(rows: ColorSpecimenConfig[], position: number) {
  const groups = grouped(rows, (row) => [getPrompt(row), row.options[position], row.design.reference]);
  const correct = groups.reduce((sum, group) => {
    const a = group.filter((row) => row.answer === "A").length;
    return sum + Math.max(a, group.length - a);
  }, 0);
  return correct / rows.length;
}

describe("direct-color controls for 0.4.0", () => {
  test("declares every controlled task and only explicit shared-image variants", () => {
    expect(SPECIMENS).toHaveLength(512);
    expect(new Set(SPECIMENS.map((row) => row.design.controlVersion))).toEqual(new Set(["0.4.0"]));
    expect(new Set(SPECIMENS.map((row) => row.imageId)).size).toBe(456);
  });

  test("same-different crosses both endpoint identities, orientation, and mapping", () => {
    const rows = SPECIMENS.filter((row) => row.family === "samediff");
    const pairs = grouped(rows, (row) => row.design.pairSetId);
    expect(pairs).toHaveLength(6);
    for (const pair of pairs) {
      expect(pair).toHaveLength(8);
      const colors = new Set(pair.flatMap((row) => row.options.map((option) => JSON.stringify(option.rgb))));
      expect(colors.size).toBe(2);
      const images = grouped(pair, (row) => row.design.mappingPairId);
      expect(images).toHaveLength(4);
      for (const image of images) {
        expect(image).toHaveLength(2);
        expect(image.map((row) => row.design.direction).sort()).toEqual(["sameA", "sameB"]);
        expect(image.map((row) => row.answer).sort()).toEqual(["A", "B"]);
        expect(new Set(image.map((row) => row.imageId)).size).toBe(1);
        expect(new Set(image.map((row) => row.groupId)).size).toBe(1);
        expect(image[0]!.options).toEqual(image[1]!.options);
      }
      for (const direction of ["sameA", "sameB"]) {
        const mapped = pair.filter((row) => row.design.direction === direction);
        expect(new Set(mapped.map((row) => JSON.stringify(row.options))).size).toBe(4);
        expect(mapped.filter((row) => row.design.same)).toHaveLength(2);
        for (const position of [0, 1]) expect(singlePatchCeiling(mapped, position)).toBe(0.5);
      }
    }
  });

  for (const family of ["lightness", "chroma"] as const) {
    test(`${family} reuses interior endpoints and bounds either single-patch predictor`, () => {
      const rows = SPECIMENS.filter((row) => row.family === family);
      const chains = grouped(rows, (row) => row.design.comparisonSetId);
      expect(rows).toHaveLength(64);
      expect(chains).toHaveLength(4);
      const dimension = family === "lightness" ? "l" : "c";
      for (const chain of chains) {
        expect(chain).toHaveLength(16);
        const colors = new Set(chain.flatMap((row) => row.options.map((option) => JSON.stringify(option.rgb))));
        expect(colors.size).toBe(5);
        const levels = [...colors].map((color) => rgbToOklch(JSON.parse(color))[dimension]).sort((a, b) => a - b);
        for (const row of chain) {
          const values = row.options.map((option) => rgbToOklch(option.rgb!)[dimension]);
          const indices = values.map((value) => levels.indexOf(value));
          expect(Math.abs(indices[0]! - indices[1]!)).toBe(1);
          expect(Math.abs(values[0]! - values[1]!)).toBeGreaterThan(0.006);
        }
        for (const direction of new Set(chain.map((row) => row.design.direction))) {
          const directed = chain.filter((row) => row.design.direction === direction);
          for (const position of [0, 1]) expect(singlePatchCeiling(directed, position)).toBe(0.625);
        }
      }
    });
  }

  test("gradient endpoints and histograms cannot identify the matching progression", () => {
    const sets = grouped(SPECIMENS.filter((row) => row.family === "gradient"), (row) => row.design.optionSetId);
    expect(sets).toHaveLength(4);
    for (const rows of sets) {
      expect(rows.map((row) => row.answer).sort()).toEqual(["A", "B", "C", "D"]);
      const fields = rows[0]!.options.map((option) => option.columns!);
      for (const field of fields) expect(field).toHaveLength(GRADIENT_WIDTH);
      expect(new Set(fields.map((field) => JSON.stringify([field[0], field.at(-1)]))).size).toBe(1);
      expect(new Set(fields.map((field) => JSON.stringify(field.map((rgb) => JSON.stringify(rgb)).sort()))).size).toBe(1);
      expect(new Set(fields.map((field) => JSON.stringify(field))).size).toBe(4);
      for (let column = 0; column < GRADIENT_WIDTH; column++) {
        const colors = fields.map((field) => JSON.stringify(field[column]));
        expect(new Set(colors).size).toBeLessThanOrEqual(2);
        for (const color of new Set(colors)) expect(colors.filter((value) => value === color).length).toBeGreaterThanOrEqual(2);
      }
      for (const row of rows) expect(row.target).toEqual(row.options["ABCD".indexOf(row.answer!)]);
    }
    const colorNecessary = sets.filter((rows) => rows[0]!.design.grayscaleMatched);
    expect(colorNecessary).toHaveLength(2);
    for (const rows of colorNecessary) {
      const gray = rows[0]!.design.reference!.grayscaleCalibration as number;
      for (const field of rows[0]!.options) {
        for (const [r, g, b] of field.columns!) {
          expect((19595 * r + 38470 * g + 7471 * b + 32768) >> 16).toBe(gray);
        }
      }
    }
  });

  test("context interventions hold task colors fixed and cross all surround positions", () => {
    const rows = SPECIMENS.filter((row) => row.family === "context");
    expect(rows).toHaveLength(80);
    const groups = grouped(rows, (row) => row.groupId);
    expect(groups).toHaveLength(16);
    for (const group of groups) {
      expect(group.map((row) => row.design.condition).sort()).toEqual(["neutral", "surround-0", "surround-1", "surround-2", "surround-3"]);
      expect(new Set(group.map((row) => row.design.interventionSetId)).size).toBe(1);
      expect(new Set(group.map((row) => JSON.stringify([row.target, row.options, row.answer]))).size).toBe(1);
      expect(new Set(group.map((row) => getPrompt(row))).size).toBe(1);
      const neutral = group.find((row) => row.design.condition === "neutral")!;
      expect(Object.values(neutral.design.surround as object)).toEqual(Array(4).fill([238, 238, 238]));
      for (const choice of "ABCD") {
        const colors = group.filter((row) => row.design.condition !== "neutral")
          .map((row) => JSON.stringify((row.design.surround as Record<string, unknown>)[choice])).sort();
        expect(colors).toEqual(CONTEXT_SURROUNDS.map((color) => JSON.stringify(color)).sort());
      }
    }
  });

  test("small-region interventions hold each palette and answer fixed across all geometries", () => {
    const rows = SPECIMENS.filter((row) => row.family === "smallmatch");
    expect(rows).toHaveLength(64);
    const groups = grouped(rows, (row) => row.groupId);
    expect(groups).toHaveLength(16);
    for (const group of groups) {
      expect(group.map((row) => row.design.condition).sort()).toEqual(["filled-20", "filled-84", "outline-12", "outline-3"]);
      expect(new Set(group.map((row) => row.design.interventionSetId)).size).toBe(1);
      expect(new Set(group.map((row) => JSON.stringify([row.target, row.options, row.answer]))).size).toBe(1);
      expect(new Set(group.map((row) => getPrompt(row))).size).toBe(1);
      expect(group.map((row) => [row.design.layout, row.design.sizePx, row.design.strokePx])).toEqual([
        ["dot", 20, 0], ["dot", 84, 0], ["frame", 84, 3], ["frame", 84, 12],
      ]);
    }
  });
});
