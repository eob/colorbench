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

// Lightness/chroma ordering sweeps: 4 separations x 2 directions x 2 positions.
for (const family of ["lightness", "chroma"] as const) {
  const separations = family === "lightness" ? [0.1, 0.05, 0.02, 0.01] : [0.06, 0.03, 0.015, 0.008];
  const directions =
    family === "lightness" ? (["lighter", "darker"] as const) : (["more", "less"] as const);
  // Even HUES entries; each lands on both positions across the chromatic cells.
  const spread4 = [HUES[0]!, HUES[2]!, HUES[4]!, HUES[6]!];
  let k = 0;
  let chromaticSeen = 0;
  for (const [level, sep] of separations.entries()) {
    for (const [directionIndex, direction] of directions.entries()) {
      for (let position = 0; position < 2; position++) {
        // Checkerboard: one gray + one chromatic per cell, 4/4 per position.
        // Aliases only the forced 3-way interaction, never the answer.
        const gray = family === "lightness" && (level + directionIndex + position) % 2 === 0;
        const cellPair = level * 2 + directionIndex;
        const hue =
          family === "lightness"
            ? gray
              ? 0
              : spread4[Math.floor(chromaticSeen++ / 2) % 4]!
            : HUES[(cellPair + position) % 8]!;
        const pair =
          family === "lightness"
            ? [fromOklch(0.62 - sep / 2, gray ? 0 : 0.06, hue), fromOklch(0.62 + sep / 2, gray ? 0 : 0.06, hue)]
            : [fromOklch(0.65, 0.055 - sep / 2, hue), fromOklch(0.65, 0.055 + sep / 2, hue)];
        const highWanted = direction === "lighter" || direction === "more";
        const correct = pair[highWanted ? 1 : 0]!;
        const wrong = pair[highWanted ? 0 : 1]!;
        const options =
          position === 0 ? [solid(correct), solid(wrong)] : [solid(wrong), solid(correct)];
        const referenceColors =
          family === "chroma"
            ? [0, 0.02, 0.04, 0.06, 0.08].map((chroma) => fromOklch(0.65, chroma, hue))
            : ([
                [48, 48, 48],
                [96, 96, 96],
                [144, 144, 144],
                [192, 192, 192],
                [232, 232, 232],
              ] as Rgb[]);
        SPECIMENS.push({
          taskId: `colorbench-${family}-${index(k)}`,
          family,
          groupId: `${family}-${index(k)}`,
          imageId: `${family}-${index(k)}`,
          options,
          answer: choices[position],
          design: {
            axis: family,
            difficulty: DIFFICULTY[level]!,
            direction,
            intendedHue: gray ? 0 : hue,
            intendedSeparation: sep,
            reference: {
              kind: family === "chroma" ? "gray-to-color" : "dark-to-light",
              colors: referenceColors,
            },
            decodedOptionOklch: options.map((option) => rgbToOklch(option.rgb!)),
          },
        });
        k += 1;
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

// Two histogram-equivalent option sets; each full field becomes R once.
for (let cell = 0; cell < 2; cell++) {
  const columns = gradientColumns(NUMERIC_TARGETS[cell]!, NUMERIC_TARGETS[cell + 3]!);
  const shifted = (offset: number): ColorField => ({
    columns: [...columns.slice(offset), ...columns.slice(0, offset)],
  });
  const options = permuteOptions([
    { columns }, { columns: [...columns].reverse() }, shifted(80), shifted(160),
  ], cell);
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
        reference: { kind: "exact-color-field", interpolation: "encoded-srgb-linear-columns", width: GRADIENT_WIDTH },
        histogramPreservingDistractors: true,
      },
    });
  }
}

// Same-different: 8 identical pairs + 8 near-threshold pairs, mappings crossed.
{
  const different: { axis: (typeof AXES)[number]; sep: number }[] = [
    { axis: "lightness", sep: 0.015 },
    { axis: "lightness", sep: 0.015 },
    { axis: "lightness", sep: 0.015 },
    { axis: "chroma", sep: 0.008 },
    { axis: "chroma", sep: 0.008 },
    { axis: "chroma", sep: 0.008 },
    { axis: "hue", sep: 6 },
    { axis: "hue", sep: 6 },
  ];
  for (let i = 0; i < 8; i++) {
    const direction = i % 2 === 0 ? "sameA" : "sameB";
    const hue = HUES[i]!;
    const rgb = fromOklch(0.65, 0.05, hue);
    SPECIMENS.push({
      taskId: `colorbench-samediff-${index(i)}`,
      family: "samediff",
      groupId: `samediff-${index(i)}`,
      imageId: `samediff-${index(i)}`,
      options: [solid(rgb), solid(rgb)],
      answer: direction === "sameA" ? "A" : "B",
      design: {
        axis: "identity",
        difficulty: "same",
        direction,
        same: true,
        intendedSeparation: 0,
        intendedHue: hue,
      },
    });
  }
  // Same hue and direction sequences as the identical block: each hue gets
  // one A trial and one B trial, so hue carries no answer information.
  different.forEach(({ axis, sep }, i) => {
    const direction = i % 2 === 0 ? "sameA" : "sameB";
    const hue = HUES[i]!;
    const base = axis === "hue" ? { l: 0.65, c: 0.09 } : { l: 0.65, c: 0.05 };
    const lo = solid(shifted(axis, base, hue, sep, 0));
    const hi = solid(shifted(axis, base, hue, sep, 1));
    if (JSON.stringify(lo) === JSON.stringify(hi))
      throw new Error(`Collapsed same-different pair on ${axis} at hue ${hue}`);
    SPECIMENS.push({
      taskId: `colorbench-samediff-${index(i + 8)}`,
      family: "samediff",
      groupId: `samediff-${index(i + 8)}`,
      imageId: `samediff-${index(i + 8)}`,
      // Lower/duller patch left in half the trials, decoupled from answer.
      options: Math.floor(i / 2) % 2 === 0 ? [lo, hi] : [hi, lo],
      answer: direction === "sameA" ? "B" : "A",
      design: {
        axis,
        difficulty: "narrow",
        direction,
        same: false,
        intendedSeparation: sep,
        intendedHue: hue,
      },
    });
  });
}

// Four option fields on fixed surrounds, each crossed with all references.
for (const [cell, hue] of CONTEXT_HUES.entries()) {
  const axis = AXES[cell % 3]!;
  const sep = axis === "lightness" ? 0.04 : axis === "chroma" ? 0.012 : 15;
  const options = permuteOptions(optionFields(axis, sep, hue), cell);
  for (let position = 0; position < 4; position++) {
    const k = cell * 4 + position;
    const target = options[position]!;
    SPECIMENS.push({
      taskId: `colorbench-context-${index(k)}`, family: "context",
      groupId: `context-${index(k)}`, imageId: `context-${index(k)}`,
      target, options, answer: choices[position],
      design: {
        axis, difficulty: "mid", sourceRgb: target.rgb,
        optionSetId: `context-${index(cell)}`,
        intendedTargetOklch: rgbToOklch(target.rgb!), intendedSeparation: sep,
        intendedHue: hue,
        surround: Object.fromEntries(choices.map((choice, i) => [choice, CONTEXT_SURROUNDS[i]])),
        reference: { kind: "surround-shift", neutralSurround: NEUTRAL },
      },
    });
  }
}

// Two geometries x two option fields x four references.
for (let cell = 0; cell < 4; cell++) {
  const layout = cell % 2 === 0 ? "dot" : "frame";
  const axis = AXES[cell % 3]!;
  const sep = axis === "lightness" ? 0.03 : axis === "chroma" ? 0.01 : 10;
  const options = permuteOptions(optionFields(axis, sep, HUES[(2 * cell) % 8]!), cell);
  for (let position = 0; position < 4; position++) {
    const k = cell * 4 + position;
    const target = options[position]!;
    SPECIMENS.push({
      taskId: `colorbench-smallmatch-${index(k)}`, family: "smallmatch",
      groupId: `smallmatch-${index(k)}`, imageId: `smallmatch-${index(k)}`,
      target, options, answer: choices[position],
      design: {
        axis, difficulty: "mid", layout, sourceRgb: target.rgb,
        optionSetId: `smallmatch-${index(cell)}`,
        intendedTargetOklch: rgbToOklch(target.rgb!), intendedSeparation: sep,
        reference: { kind: "small-region", neutralSurround: NEUTRAL },
      },
    });
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
SPECIMENS.sort((a, b) => a.taskId.localeCompare(b.taskId));
