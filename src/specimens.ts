import { fromOklch, rgbToOklch } from "./colors.ts";
import type { Choice, ColorField, ColorSpecimenConfig, Rgb } from "./types.ts";

export const GRADIENT_WIDTH = 240;
export const NUMERIC_TARGETS: Rgb[] = [
  [192, 64, 80],
  [38, 112, 190],
  [60, 140, 100],
  [185, 135, 45],
  [135, 85, 175],
  [22, 48, 75],
  [225, 215, 188],
  [128, 128, 128],
  [230, 32, 44],
  [24, 158, 82],
  [44, 84, 228],
  [236, 208, 44],
  [198, 58, 188],
  [44, 178, 198],
  [16, 16, 18],
  [243, 243, 240],
];
const HUES = [25, 70, 115, 160, 205, 250, 295, 340];
export const CONTEXT_HUES = [25, 115, 205, 295];
export const CONTEXT_SURROUNDS: Rgb[] = [
  fromOklch(0.25, 0, 0),
  fromOklch(0.85, 0.03, 80),
  fromOklch(0.6, 0.15, 30),
  fromOklch(0.6, 0.09, 220),
];
const MATCH_SEPS: Record<"lightness" | "chroma" | "hue", number[]> = {
  lightness: [0.08, 0.04, 0.02, 0.01],
  chroma: [0.025, 0.012, 0.007, 0.004],
  hue: [35, 15, 8, 4],
};
const AXES = ["lightness", "chroma", "hue"] as const;
const DIFFICULTY = ["wide", "mid", "narrow", "near"];
const NEUTRAL: Rgb = [238, 238, 238];
const choices: Choice[] = ["A", "B", "C", "D"];
const solid = (rgb: Rgb): ColorField => ({ rgb });
const index = (i: number) => String(i + 1).padStart(2, "0");
// Every option set is reused with all four references. The balanced rotations
// also distribute coordinate rank independently of answer position.
function permuteOptions(fields: ColorField[], cell: number): ColorField[] {
  const orders = [[2, 0, 3, 1], [1, 3, 0, 2], [0, 2, 1, 3]];
  const order = orders[Math.floor(cell / 4) % orders.length]!;
  return Array.from({ length: 4 }, (_, i) => fields[order[(i + cell) % 4]!]!);
}
function shifted(
  axis: (typeof AXES)[number],
  base: { l: number; c: number },
  hue: number,
  sep: number,
  multiplier: number,
): Rgb {
  return fromOklch(
    base.l + (axis === "lightness" ? multiplier * sep : 0),
    base.c + (axis === "chroma" ? multiplier * sep : 0),
    hue + (axis === "hue" ? multiplier * sep : 0),
  );
}
function optionFields(axis: (typeof AXES)[number], sep: number, hue: number): ColorField[] {
  for (const l of [0.65, 0.7, 0.6]) {
    for (const c of axis === "chroma" ? [0.055, 0.06, 0.05] : [0.075, 0.06, 0.05]) {
      try {
        const fields = [-1.5, -0.5, 0.5, 1.5].map((m) => solid(shifted(axis, { l, c }, hue, sep, m)));
        if (new Set(fields.map((f) => JSON.stringify(f.rgb))).size === 4) return fields;
      } catch {
        // Try the next declared in-gamut center; never clip construction colors.
      }
    }
  }
  throw new Error(`Unresolvable ${axis} separation ${sep} at hue ${hue}`);
}
export function gradientColumns(a: Rgb, b: Rgb): Rgb[] {
  return Array.from(
    { length: GRADIENT_WIDTH },
    (_, x) =>
      a.map((value, c) => Math.round(value + ((b[c]! - value) * x) / (GRADIENT_WIDTH - 1))) as Rgb,
  );
}
export const SPECIMENS: ColorSpecimenConfig[] = [];

// Three axes x four separations x four references; the option field is fixed
// within each cell, so no rule that ignores R can beat uniform guessing.
{
  let n = 0;
  for (const [axisIndex, axis] of AXES.entries()) {
    for (const [level, sep] of MATCH_SEPS[axis].entries()) {
      const cell = axisIndex * 4 + level;
      const options = permuteOptions(optionFields(axis, sep, HUES[cell % 8]!), cell);
      for (let position = 0; position < 4; position++) {
        const target = options[position]!;
        const id = index(n++);
        for (const family of ["matching", "binding"] as const) {
          SPECIMENS.push({
            taskId: `colorbench-${family}-${id}`, family,
            groupId: `match-binding-${id}`, imageId: `${family}-${id}`,
            target, options, answer: choices[position],
            design: {
              axis, difficulty: DIFFICULTY[level]!, sourceRgb: target.rgb,
              optionSetId: `matching-${index(cell)}`,
              pairedFamily: family === "matching" ? "binding" : "matching",
              intendedTargetOklch: rgbToOklch(target.rgb!), intendedSeparation: sep,
              reference: { kind: "exact-visible-color", neutralSurround: NEUTRAL },
            },
          });
        }
      }
    }
  }
}

// Adjacent chains reuse each interior color as both the lower and higher
// endpoint. Even a memorized one-patch rule is bounded at 5/8 within a chain.
for (const family of ["lightness", "chroma"] as const) {
  const separations = family === "lightness" ? [0.1, 0.05, 0.02, 0.01] : [0.06, 0.03, 0.015, 0.008];
  const directions = family === "lightness" ? (["lighter", "darker"] as const) : (["more", "less"] as const);
  const chains = family === "lightness"
    ? [{ l: 0.36, c: 0, h: 0 }, { l: 0.43, c: 0.05, h: 25 },
       { l: 0.50, c: 0.05, h: 115 }, { l: 0.58, c: 0.05, h: 295 }]
    : [{ l: 0.65, c: 0.012, h: 25 }, { l: 0.70, c: 0.008, h: 70 },
       { l: 0.66, c: 0.016, h: 145 }, { l: 0.64, c: 0.020, h: 295 }];
  let k = 0;
  for (const [cell, base] of chains.entries()) {
    const gaps = separations.map((_, edge) => separations[(edge + cell) % 4]!);
    const values = [family === "lightness" ? base.l : base.c];
    for (const gap of gaps) values.push(values.at(-1)! + gap);
    const fields = values.map((value) => solid(fromOklch(
      family === "lightness" ? value : base.l,
      family === "chroma" ? value : base.c, base.h,
    )));
    const dimension = family === "lightness" ? "l" : "c";
    for (let edge = 0; edge < 4; edge++) {
      if (rgbToOklch(fields[edge + 1]!.rgb!)[dimension] <= rgbToOklch(fields[edge]!.rgb!)[dimension])
        throw new Error(`Collapsed ${family} chain ${cell} at edge ${edge}`);
      for (const direction of directions) {
        for (let orientation = 0; orientation < 2; orientation++) {
          const options = orientation === 0
            ? [fields[edge]!, fields[edge + 1]!]
            : [fields[edge + 1]!, fields[edge]!];
          const highWanted = direction === "lighter" || direction === "more";
          const position = highWanted ? 1 - orientation : orientation;
          const referenceColors = family === "chroma"
            ? [0, 0.02, 0.04, 0.06, 0.08].map((chroma) => fromOklch(base.l, chroma, base.h))
            : [[48, 48, 48], [96, 96, 96], [144, 144, 144], [192, 192, 192], [232, 232, 232]] as Rgb[];
          SPECIMENS.push({
            taskId: `colorbench-${family}-${index(k)}`, family,
            groupId: `${family}-chain-${index(cell)}-edge-${index(edge)}`,
            imageId: `${family}-${index(k)}`, options, answer: choices[position],
            design: {
              axis: family, difficulty: DIFFICULTY[separations.indexOf(gaps[edge]!)]!, direction,
              comparisonSetId: `${family}-chain-${index(cell)}`,
              intendedHue: base.h, intendedSeparation: gaps[edge],
              reference: { kind: family === "chroma" ? "gray-to-color" : "dark-to-light", colors: referenceColors },
              decodedOptionOklch: options.map((option) => rgbToOklch(option.rgb!)),
            },
          });
          k += 1;
        }
      }
    }
  }
}

// Four separations x two lightness/chroma contexts x four references.
for (const [level, sep] of [70, 30, 12, 6].entries()) {
  for (const varying of [false, true]) {
    const cell = level * 2 + Number(varying);
    const baseHue = HUES[(2 * level) % 8]!;
    const fields = Array.from({ length: 4 }, (_, j) => solid(fromOklch(
      varying ? [0.55, 0.73, 0.59, 0.69][j]! : 0.65,
      varying ? [0.045, 0.07, 0.055, 0.065][j]! : 0.075,
      baseHue + j * sep,
    )));
    const options = permuteOptions(fields, cell);
    for (let position = 0; position < 4; position++) {
      const k = cell * 4 + position;
      const hue = rgbToOklch(options[position]!.rgb!).h;
      const target = varying ? solid(fromOklch(0.65, 0.075, hue)) : options[position]!;
      SPECIMENS.push({
        taskId: `colorbench-hue-${index(k)}`, family: "hue",
        groupId: `hue-${index(k)}`, imageId: `hue-${index(k)}`,
        target, options, answer: choices[position],
        design: {
          axis: "hue", difficulty: varying ? "varying-lightness-chroma" : "fixed-lightness-chroma",
          optionSetId: `hue-${index(cell)}`, sourceRgb: target.rgb,
          intendedHue: hue, intendedSeparation: sep,
          reference: { kind: "hue-reference", minimumDistractorDegrees: sep },
          humanAgreementMeasured: false,
        },
      });
    }
  }
}

// Shared endcaps and histograms remove endpoint/set matching. Two independent
// interior swaps also prevent any single column from distinguishing all options.
const gradientPalettes: { a: Rgb; b: Rgb; gray?: number }[] = [
  { a: NUMERIC_TARGETS[0]!, b: NUMERIC_TARGETS[3]! },
  { a: NUMERIC_TARGETS[1]!, b: NUMERIC_TARGETS[4]! },
  { a: [144, 120, 120], b: [120, 120, 180], gray: 127 },
  { a: [210, 142, 120], b: [140, 160, 210], gray: 160 },
];
for (const [cell, palette] of gradientPalettes.entries()) {
  const columns = gradientColumns(palette.a, palette.b).map((rgb): Rgb => {
    if (palette.gray === undefined) return rgb;
    // Quantized Pillow-L control: solve the green channel after interpolation
    // instead of assuming equal-gray endpoints retain equal gray after rounding.
    const green = Math.round((palette.gray - 0.299 * rgb[0] - 0.114 * rgb[2]) / 0.587);
    if (green < 0 || green > 255) throw new Error("Grayscale control leaves the sRGB gamut");
    return [rgb[0], green, rgb[2]];
  });
  const blocks = Array.from({ length: 4 }, (_, block) => columns.slice(4 + block * 58, 4 + (block + 1) * 58));
  const options = permuteOptions([[0, 1, 2, 3], [1, 0, 2, 3], [0, 1, 3, 2], [1, 0, 3, 2]].map((order) => ({
    columns: [...columns.slice(0, 4), ...order.flatMap((block) => blocks[block]!), ...columns.slice(-4)],
  })), cell);
  for (let position = 0; position < 4; position++) {
    const k = cell * 4 + position;
    const target = options[position]!;
    SPECIMENS.push({
      taskId: `colorbench-gradient-${index(k)}`, family: "gradient",
      groupId: `gradient-${index(k)}`, imageId: `gradient-${index(k)}`,
      target, options, answer: choices[position],
      design: {
        axis: "spatial-color-progression", difficulty: `set-${cell + 1}`,
        optionSetId: `gradient-${index(cell)}`, sourceRgb: target.columns![0],
        reference: { kind: "exact-color-field", interpolation: "encoded-srgb-linear-columns", width: GRADIENT_WIDTH,
          interiorPermutation: "two-independent-block-swaps", grayscaleCalibration: palette.gray ?? null },
        histogramPreservingDistractors: true, endpointMatched: true,
        grayscaleMatched: palette.gray !== undefined,
      },
    });
  }
}

// Reuse both endpoint colors in identical and differing pairs under both
// answer mappings: either patch alone carries exactly zero label information.
const equalityPairs = [
  { axis: "lightness", l: 0.50, c: 0.04, h: 25, sep: 0.015 },
  { axis: "lightness", l: 0.73, c: 0.065, h: 205, sep: 0.015 },
  { axis: "chroma", l: 0.60, c: 0.035, h: 115, sep: 0.008 },
  { axis: "chroma", l: 0.72, c: 0.075, h: 295, sep: 0.008 },
  { axis: "hue", l: 0.58, c: 0.08, h: 70, sep: 6 },
  { axis: "hue", l: 0.70, c: 0.06, h: 250, sep: 6 },
] as const;
for (const [cell, pair] of equalityPairs.entries()) {
  const a = solid(shifted(pair.axis, pair, pair.h, pair.sep, 0));
  const b = solid(shifted(pair.axis, pair, pair.h, pair.sep, 1));
  if (JSON.stringify(a) === JSON.stringify(b)) throw new Error(`Collapsed same-different pair ${cell}`);
  const pairings = [{ name: "aa", options: [a, a] }, { name: "bb", options: [b, b] },
    { name: "ab", options: [a, b] }, { name: "ba", options: [b, a] }];
  for (const [combination, { name, options }] of pairings.entries()) {
    const same = combination < 2;
    const mappingPairId = `samediff-pair-${index(cell)}-${name}`;
    for (const [mapping, direction] of (["sameA", "sameB"] as const).entries()) {
      const k = cell * 8 + combination * 2 + mapping;
      SPECIMENS.push({
        taskId: `colorbench-samediff-${index(k)}`, family: "samediff",
        groupId: mappingPairId, imageId: mappingPairId,
        options, answer: (same === (direction === "sameA")) ? "A" : "B",
        design: {
          axis: same ? "identity" : pair.axis, difficulty: same ? "same" : "narrow",
          pairSetId: `samediff-pair-${index(cell)}`, mappingPairId,
          direction, same, intendedSeparation: same ? 0 : pair.sep, intendedHue: pair.h,
        },
      });
    }
  }
}

// Each fixed option field is tested on neutral surrounds and every cyclic
// surround assignment; reference/answer stay paired across interventions.
for (const [cell, hue] of CONTEXT_HUES.entries()) {
  const axis = AXES[cell % 3]!;
  const sep = axis === "lightness" ? 0.04 : axis === "chroma" ? 0.012 : 15;
  const options = permuteOptions(optionFields(axis, sep, hue), cell);
  for (let intervention = 0; intervention < 5; intervention++) {
    const condition = intervention === 0 ? "neutral" : `surround-${intervention - 1}`;
    for (let position = 0; position < 4; position++) {
      const k = cell * 20 + intervention * 4 + position;
      const target = options[position]!;
      SPECIMENS.push({
        taskId: `colorbench-context-${index(k)}`, family: "context",
        groupId: `context-${index(cell)}-reference-${choices[position]!.toLowerCase()}`, imageId: `context-${index(k)}`,
        target, options, answer: choices[position],
        design: {
          axis, difficulty: "mid", sourceRgb: target.rgb,
          interventionSetId: `context-${index(cell)}`, condition,
          optionSetId: `context-${index(cell)}-${condition}`,
          intendedTargetOklch: rgbToOklch(target.rgb!), intendedSeparation: sep, intendedHue: hue,
          surround: Object.fromEntries(choices.map((choice, i) => [choice,
            intervention === 0 ? NEUTRAL : CONTEXT_SURROUNDS[(i + intervention - 1) % 4]!])),
          reference: { kind: "surround-shift", neutralSurround: NEUTRAL },
        },
      });
    }
  }
}

// Cross the same four color fields with filled size and outline thickness,
// keeping colors, reference rank, and answer fixed for every intervention.
const smallConditions = [
  { condition: "filled-20", layout: "dot", sizePx: 20, strokePx: 0 },
  { condition: "filled-84", layout: "dot", sizePx: 84, strokePx: 0 },
  { condition: "outline-3", layout: "frame", sizePx: 84, strokePx: 3 },
  { condition: "outline-12", layout: "frame", sizePx: 84, strokePx: 12 },
];
for (let cell = 0; cell < 4; cell++) {
  const axis = AXES[cell % 3]!;
  const sep = axis === "lightness" ? 0.03 : axis === "chroma" ? 0.01 : 10;
  const options = permuteOptions(optionFields(axis, sep, HUES[(2 * cell) % 8]!), cell);
  for (const [intervention, condition] of smallConditions.entries()) {
    for (let position = 0; position < 4; position++) {
      const k = cell * 16 + intervention * 4 + position;
      const target = options[position]!;
      SPECIMENS.push({
        taskId: `colorbench-smallmatch-${index(k)}`, family: "smallmatch",
        groupId: `smallmatch-${index(cell)}-reference-${choices[position]!.toLowerCase()}`, imageId: `smallmatch-${index(k)}`,
        target, options, answer: choices[position],
        design: {
          axis, difficulty: "mid", ...condition, sourceRgb: target.rgb,
          interventionSetId: `smallmatch-${index(cell)}`, optionSetId: `smallmatch-${index(cell)}-${condition.condition}`,
          intendedTargetOklch: rgbToOklch(target.rgb!), intendedSeparation: sep,
          reference: { kind: "small-region", neutralSurround: NEUTRAL },
        },
      });
    }
  }
}

for (let i = 0; i < NUMERIC_TARGETS.length; i++) {
  for (const family of ["rgb", "hsl", "oklch"] as const) {
    SPECIMENS.push({
      taskId: `colorbench-${family}-${index(i)}`,
      family,
      groupId: `numeric-${index(i)}`,
      imageId: `numeric-${index(i)}`,
      target: solid(NUMERIC_TARGETS[i]!),
      options: [],
      design: {
        axis: "numeric-estimation",
        difficulty: i === 7 ? "achromatic" : i >= 14 ? "near-neutral" : "chromatic",
        sourceRgb: NUMERIC_TARGETS[i],
        reference: { kind: "unreferenced-estimation", neutralSurround: NEUTRAL },
      },
    });
  }
}
for (const specimen of SPECIMENS) specimen.design.controlVersion = "0.4.0";
SPECIMENS.sort((a, b) => a.taskId.localeCompare(b.taskId));
