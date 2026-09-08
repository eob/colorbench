import { describe, expect, test } from "bun:test";
import { SPECIMENS } from "./specimens.ts";

describe("ColorBench Specimens", () => {
  test("generates exactly 100 specimens", () => {
    expect(SPECIMENS.length).toBe(100);
  });

  test("assigns unique IDs to each specimen", () => {
    const ids = new Set(SPECIMENS.map((s) => s.id));
    expect(ids.size).toBe(100);
  });

  test("covers all semantic roles", () => {
    const roles = new Set(SPECIMENS.map((s) => s.semantic_role));
    expect(roles.has("primary")).toBe(true);
    expect(roles.has("secondary")).toBe(true);
    expect(roles.has("success")).toBe(true);
    expect(roles.has("warning")).toBe(true);
    expect(roles.has("danger")).toBe(true);
    expect(roles.has("info")).toBe(true);
  });

  test("covers all contrast tiers", () => {
    const tiers = new Set(SPECIMENS.map((s) => s.contrast_tier));
    expect(tiers.has("aaa-high")).toBe(true);
    expect(tiers.has("aa-standard")).toBe(true);
    expect(tiers.has("large-text-subdued")).toBe(true);
    expect(tiers.has("failing-disabled")).toBe(true);
  });

  test("covers all fill types", () => {
    const fills = new Set(SPECIMENS.map((s) => s.fill_type));
    expect(fills.has("solid")).toBe(true);
    expect(fills.has("linear-gradient")).toBe(true);
    expect(fills.has("outline-transparent")).toBe(true);
  });
});
