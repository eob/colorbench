import { expect, test } from "bun:test";
import { SPECIMENS } from "./specimens.ts";

// A predictor receives every option but no reference. Identical inputs must
// cover all four answers, so even arbitrary option-only rules score 25%.
for (const family of ["matching", "binding", "context", "smallmatch", "hue", "gradient"]) {
  test(`${family}: every identical option field has all four reference answers`, () => {
    const groups = new Map<string, string[]>();
    for (const item of SPECIMENS.filter((s) => s.family === family)) {
      const key = JSON.stringify([item.options, item.design.layout, item.design.sizePx, item.design.strokePx, item.design.surround]);
      groups.set(key, [...(groups.get(key) ?? []), item.answer!]);
    }
    for (const answers of groups.values()) expect(answers.sort()).toEqual(["A", "B", "C", "D"]);
  });
}
