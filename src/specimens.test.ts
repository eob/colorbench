import { describe, expect, test } from "bun:test";
import { SPECIMENS } from "./specimens.ts";

describe("perception pilot design", () => {
  test("contains eight questions in each of nine families", () => {
    expect(SPECIMENS).toHaveLength(72);
    expect(new Set(SPECIMENS.map((s) => s.taskId)).size).toBe(72);
    for (const family of [
      "matching",
      "lightness",
      "chroma",
      "hue",
      "binding",
      "gradient",
      "rgb",
      "hsl",
      "oklch",
    ]) {
      expect(SPECIMENS.filter((s) => s.family === family)).toHaveLength(8);
    }
  });
  test("balances every choice location within a family", () => {
    for (const family of ["matching", "lightness", "chroma", "hue", "binding", "gradient"]) {
      const examples = SPECIMENS.filter((s) => s.family === family);
      const choices = ["lightness", "chroma"].includes(family) ? ["A", "B"] : ["A", "B", "C", "D"];
      for (const choice of choices)
        expect(examples.filter((s) => s.answer === choice)).toHaveLength(8 / choices.length);
    }
  });
  test("numeric formats share their target recipe and stimulus group", () => {
    const numeric = SPECIMENS.filter((s) => ["rgb", "hsl", "oklch"].includes(s.family));
    const groups = new Set(numeric.map((s) => s.groupId));
    expect(groups.size).toBe(8);
    for (const id of groups) {
      const group = numeric.filter((s) => s.groupId === id);
      expect(group.map((s) => s.family).sort()).toEqual(["hsl", "oklch", "rgb"]);
      expect(new Set(group.map((s) => JSON.stringify(s.target))).size).toBe(1);
      expect(new Set(group.map((s) => s.imageId)).size).toBe(1);
    }
  });
});
