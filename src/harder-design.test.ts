import { describe, expect, test } from "bun:test";
import { hueDistance, rgbToOklch } from "./colors.ts";
import { SPECIMENS } from "./specimens.ts";

const COUNTS: Record<string, number> = {
  matching: 48,
  binding: 48,
  lightness: 16,
  chroma: 16,
  hue: 16,
  gradient: 8,
  samediff: 16,
  context: 16,
  smallmatch: 16,
  rgb: 16,
  hsl: 16,
  oklch: 16,
};

describe("harder 0.3.0 corpus design", () => {
  test("contains the frozen 248-question corpus", () => {
    expect(SPECIMENS).toHaveLength(248);
    expect(new Set(SPECIMENS.map((s) => s.taskId)).size).toBe(248);
    expect(new Set(SPECIMENS.map((s) => s.imageId)).size).toBe(216);
    for (const [family, count] of Object.entries(COUNTS))
      expect(SPECIMENS.filter((s) => s.family === family)).toHaveLength(count);
  });
  test("balances every choice location within a family", () => {
    for (const family of [
      "matching",
      "lightness",
      "chroma",
      "hue",
      "binding",
      "gradient",
      "samediff",
      "context",
      "smallmatch",
    ]) {
      const examples = SPECIMENS.filter((s) => s.family === family);
      expect(examples.length).toBeGreaterThan(0);
      const choices = ["lightness", "chroma", "samediff"].includes(family)
        ? ["A", "B"]
        : ["A", "B", "C", "D"];
      for (const choice of choices)
        expect(examples.filter((s) => s.answer === choice)).toHaveLength(
          examples.length / choices.length,
        );
    }
  });
  test("crosses every sweep separation with every answer position", () => {
    for (const family of ["matching", "binding"]) {
      const examples = SPECIMENS.filter((s) => s.family === family);
      const cells = new Map<string, string[]>();
      for (const s of examples) {
        const key = `${s.design.axis}@${s.design.intendedSeparation}`;
        cells.set(key, [...(cells.get(key) ?? []), s.answer!]);
      }
      expect(cells.size).toBe(12);
      for (const answers of cells.values()) expect(answers.sort()).toEqual(["A", "B", "C", "D"]);
    }
    for (const family of ["lightness", "chroma"]) {
      const examples = SPECIMENS.filter((s) => s.family === family);
      const cells = new Map<string, string[]>();
      for (const s of examples) {
        const key = `${s.design.intendedSeparation}@${s.design.direction}`;
        cells.set(key, [...(cells.get(key) ?? []), s.answer!]);
      }
      expect(cells.size).toBe(8);
      for (const answers of cells.values()) expect(answers.sort()).toEqual(["A", "B"]);
    }
    const hues = SPECIMENS.filter((s) => s.family === "hue");
    const hueCells = new Map<number, { answers: string[]; fixed: number; varying: number }>();
    for (const s of hues) {
      const sep = s.design.intendedSeparation as number;
      const cell = hueCells.get(sep) ?? { answers: [], fixed: 0, varying: 0 };
      cell.answers.push(s.answer!);
      if (s.design.difficulty === "fixed-lightness-chroma") cell.fixed += 1;
      else cell.varying += 1;
      hueCells.set(sep, cell);
    }
    expect([...hueCells.keys()].sort((a, b) => a - b)).toEqual([6, 12, 30, 70]);
    for (const cell of hueCells.values()) {
      expect(cell.answers.sort()).toEqual(["A", "B", "C", "D"]);
      expect([cell.fixed, cell.varying]).toEqual([2, 2]);
    }
  });
  test("crosses equality, surrounds, and layouts with positions", () => {
    const sames = SPECIMENS.filter((s) => s.family === "samediff");
    const cells = new Map<string, number>();
    for (const s of sames) {
      const key = `${s.design.same}@${s.design.direction}`;
      cells.set(key, (cells.get(key) ?? 0) + 1);
    }
    expect(cells.size).toBe(4);
    for (const count of cells.values()) expect(count).toBe(4);
    const contexts = SPECIMENS.filter((s) => s.family === "context");
    expect(new Set(contexts.map((s) => s.design.intendedHue)).size).toBe(4);
    const perHue = new Map<number, string[]>();
    for (const s of contexts) {
      const hue = s.design.intendedHue as number;
      perHue.set(hue, [...(perHue.get(hue) ?? []), s.answer!]);
    }
    for (const answers of perHue.values()) expect(answers.sort()).toEqual(["A", "B", "C", "D"]);
    const smalls = SPECIMENS.filter((s) => s.family === "smallmatch");
    const layoutCells = new Map<string, number>();
    for (const s of smalls) {
      const key = `${s.design.layout}@${s.answer}`;
      layoutCells.set(key, (layoutCells.get(key) ?? 0) + 1);
    }
    expect(layoutCells.size).toBe(8);
    for (const count of layoutCells.values()) expect(count).toBe(2);
  });
  test("pairs matching with binding and numeric formats with shared bytes", () => {
    const pairs = SPECIMENS.filter((s) => ["matching", "binding"].includes(s.family));
    const groups = new Set(pairs.map((s) => s.groupId));
    expect(groups.size).toBe(48);
    for (const id of groups) {
      const group = pairs.filter((s) => s.groupId === id);
      expect(group.map((s) => s.family).sort()).toEqual(["binding", "matching"]);
      expect(JSON.stringify(group[0]!.target)).toBe(JSON.stringify(group[1]!.target));
      expect(JSON.stringify(group[0]!.options)).toBe(JSON.stringify(group[1]!.options));
      expect(group[0]!.answer).toBe(group[1]!.answer);
    }
    const numeric = SPECIMENS.filter((s) => ["rgb", "hsl", "oklch"].includes(s.family));
    const numericGroups = new Set(numeric.map((s) => s.groupId));
    expect(numericGroups.size).toBe(16);
    for (const id of numericGroups) {
      const group = numeric.filter((s) => s.groupId === id);
      expect(group.map((s) => s.family).sort()).toEqual(["hsl", "oklch", "rgb"]);
      expect(new Set(group.map((s) => JSON.stringify(s.target))).size).toBe(1);
      expect(new Set(group.map((s) => s.imageId)).size).toBe(1);
    }
  });
  test("keeps every exact-match target distinct from its distractors", () => {
    for (const s of SPECIMENS.filter((st) =>
      ["matching", "binding", "context", "smallmatch"].includes(st.family),
    )) {
      // Options embed the target once; pairwise-distinct options imply the
      // target differs from every distractor.
      const colors = s.options.map((o) => JSON.stringify(o.rgb ?? o.columns));
      expect(new Set(colors).size).toBe(4);
      expect(colors).toContain(JSON.stringify(s.target!.rgb ?? s.target!.columns));
    }
  });
  test("records decoded ordering gaps near the intended separations", () => {
    for (const s of SPECIMENS.filter((st) => ["lightness", "chroma"].includes(st.family))) {
      const dimension = s.family === "lightness" ? "l" : "c";
      const values = s.options.map((o) => rgbToOklch(o.rgb!)[dimension]);
      const gap = Math.abs(values[0]! - values[1]!);
      const intended = s.design.intendedSeparation as number;
      expect(gap).toBeGreaterThan(0.006);
      expect(Math.abs(gap - intended)).toBeLessThanOrEqual(Math.max(0.01, 0.35 * intended));
    }
    for (const s of SPECIMENS.filter((st) => st.family === "samediff" && !st.design.same)) {
      const [a, b] = s.options.map((o) => rgbToOklch(o.rgb!));
      const axis = s.design.axis as string;
      const dimension = axis === "lightness" ? "l" : "c";
      const gap = axis === "hue" ? hueDistance(a!.h, b!.h) : Math.abs(a![dimension] - b![dimension]);
      const intended = s.design.intendedSeparation as number;
      const tolerance = axis === "hue" ? Math.max(2.5, 0.35 * intended) : Math.max(0.01, 0.35 * intended);
      expect(Math.abs(gap - intended)).toBeLessThanOrEqual(tolerance);
    }
    for (const s of SPECIMENS.filter((st) => st.family === "samediff" && st.design.same))
      expect(JSON.stringify(s.options[0])).toBe(JSON.stringify(s.options[1]));
  });
  test("hue winners share decoded pixels and runners-up track the minimum", () => {
    for (const s of SPECIMENS.filter((st) => st.family === "hue")) {
      const target = rgbToOklch(s.target!.rgb!);
      const errors = s.options.map((o) => hueDistance(rgbToOklch(o.rgb!).h, target.h));
      const ordered = [...errors].sort((a, b) => a - b);
      const minimum = (s.design.reference as Record<string, number>).minimumDistractorDegrees!;
      expect(ordered[0]).toBeLessThanOrEqual(1);
      expect(ordered[1]! - ordered[0]!).toBeGreaterThanOrEqual(2.5);
      expect(Math.abs(ordered[1]! - minimum)).toBeLessThanOrEqual(Math.max(2.5, 0.35 * minimum));
    }
  });
});
