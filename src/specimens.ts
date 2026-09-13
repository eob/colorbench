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
];
const HUES = [25, 70, 115, 160, 205, 250, 295, 340];
const choices: Choice[] = ["A", "B", "C", "D"];
const solid = (rgb: Rgb): ColorField => ({ rgb });
const index = (i: number) => String(i + 1).padStart(2, "0");
function optionsWithAnswer(
  target: ColorField,
  distractors: ColorField[],
  position: number,
): ColorField[] {
  const options = [...distractors];
  options.splice(position, 0, target);
  return options;
}
export function gradientColumns(a: Rgb, b: Rgb): Rgb[] {
  return Array.from(
    { length: GRADIENT_WIDTH },
    (_, x) =>
      a.map((value, c) => Math.round(value + ((b[c]! - value) * x) / (GRADIENT_WIDTH - 1))) as Rgb,
  );
}
export const SPECIMENS: ColorSpecimenConfig[] = [];

for (let i = 0; i < 8; i++) {
  const hue = HUES[i]!;
  const axis = ["lightness", "chroma", "hue"][i % 3]!;
  const difficulty = i % 2 === 0 ? "wide" : "narrow";
  const l = 0.65,
    c = 0.05;
  const target = solid(fromOklch(l, c, hue));
  const delta =
    axis === "lightness"
      ? difficulty === "wide"
        ? 0.08
        : 0.04
      : axis === "chroma"
        ? difficulty === "wide"
          ? 0.025
          : 0.012
        : difficulty === "wide"
          ? 35
          : 15;
  const distractors = [-1, 1, 2].map((multiplier) =>
    solid(
      fromOklch(
        l + (axis === "lightness" ? multiplier * delta : 0),
        c + (axis === "chroma" ? multiplier * delta : 0),
        hue + (axis === "hue" ? multiplier * delta : 0),
      ),
    ),
  );
  const options = optionsWithAnswer(target, distractors, i % 4);
  for (const family of ["matching", "binding"] as const) {
    SPECIMENS.push({
      taskId: `colorbench-${family}-${index(i)}`,
      family,
      groupId: `match-binding-${index(i)}`,
      imageId: `${family}-${index(i)}`,
      target,
      options,
      answer: choices[i % 4],
      design: {
        axis,
        difficulty,
        sourceRgb: target.rgb,
        pairedFamily: family === "matching" ? "binding" : "matching",
        intendedTargetOklch: { l, c, h: hue },
        intendedSeparation: delta,
        reference: { kind: "exact-visible-color", neutralSurround: [238, 238, 238] },
      },
    });
  }
}
for (const family of ["lightness", "chroma"] as const) {
  for (let i = 0; i < 8; i++) {
    const direction =
      family === "lightness" ? (i % 4 < 2 ? "lighter" : "darker") : i % 4 < 2 ? "more" : "less";
    const difficulty = i < 4 ? "wide" : "narrow";
    const hue = HUES[i]!;
    const values =
      family === "lightness"
        ? [
            fromOklch(i < 4 ? 0.5 : 0.59, i < 2 ? 0 : 0.06, hue),
            fromOklch(i < 4 ? 0.74 : 0.69, i < 2 ? 0 : 0.06, hue),
          ]
        : [fromOklch(0.65, i < 4 ? 0.025 : 0.05, hue), fromOklch(0.65, i < 4 ? 0.09 : 0.08, hue)];
    const highWanted = direction === "lighter" || direction === "more";
    const correct = values[highWanted ? 1 : 0]!;
    const wrong = values[highWanted ? 0 : 1]!;
    const options = i % 2 === 0 ? [solid(correct), solid(wrong)] : [solid(wrong), solid(correct)];
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
      taskId: `colorbench-${family}-${index(i)}`,
      family,
      groupId: `${family}-${index(i)}`,
      imageId: `${family}-${index(i)}`,
      options,
      answer: choices[i % 2],
      design: {
        axis: family,
        difficulty,
        direction,
        intendedHue: hue,
        reference: {
          kind: family === "chroma" ? "gray-to-color" : "dark-to-light",
          colors: referenceColors,
        },
        decodedOptionOklch: options.map((option) => rgbToOklch(option.rgb!)),
      },
    });
  }
}
for (let i = 0; i < 8; i++) {
  const hue = HUES[i]!;
  const target = solid(fromOklch(0.65, 0.075, hue));
  const varying = i >= 4;
  const optionHues = [hue, hue + 70, hue + 160, hue + 260];
  const fields = optionHues.map((h, j) =>
    solid(
      fromOklch(
        varying ? [0.55, 0.73, 0.59, 0.69][(j + i) % 4]! : 0.65,
        varying ? [0.045, 0.07, 0.055, 0.065][(j + i) % 4]! : 0.075,
        h,
      ),
    ),
  );
  SPECIMENS.push({
    taskId: `colorbench-hue-${index(i)}`,
    family: "hue",
    groupId: `hue-${index(i)}`,
    imageId: `hue-${index(i)}`,
    target,
    options: optionsWithAnswer(fields[0]!, fields.slice(1), i % 4),
    answer: choices[i % 4],
    design: {
      axis: "hue",
      difficulty: varying ? "varying-lightness-chroma" : "fixed-lightness-chroma",
      sourceRgb: target.rgb,
      intendedHue: hue,
      reference: { kind: "hue-reference", minimumDistractorDegrees: 70 },
      humanAgreementMeasured: false,
    },
  });
}
for (let i = 0; i < 8; i++) {
  const a = NUMERIC_TARGETS[i]!,
    b = NUMERIC_TARGETS[(i + 3) % 8]!;
  const forward = gradientColumns(a, b);
  const columns = i % 2 === 0 ? forward : [...forward].reverse();
  const target = { columns };
  const shifted = (offset: number): ColorField => ({
    columns: [...columns.slice(offset), ...columns.slice(0, offset)],
  });
  const options = optionsWithAnswer(
    target,
    [{ columns: [...columns].reverse() }, shifted(80), shifted(160)],
    i % 4,
  );
  SPECIMENS.push({
    taskId: `colorbench-gradient-${index(i)}`,
    family: "gradient",
    groupId: `gradient-${index(i)}`,
    imageId: `gradient-${index(i)}`,
    target,
    options,
    answer: choices[i % 4],
    design: {
      axis: "spatial-color-progression",
      difficulty: i % 2 === 0 ? "forward" : "reverse",
      sourceRgb: columns[0],
      reference: {
        kind: "exact-color-field",
        interpolation: "encoded-srgb-linear-columns",
        width: GRADIENT_WIDTH,
      },
      histogramPreservingDistractors: true,
    },
  });
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
        difficulty: i === 7 ? "achromatic" : "chromatic",
        sourceRgb: NUMERIC_TARGETS[i],
        reference: { kind: "unreferenced-estimation", neutralSurround: [238, 238, 238] },
      },
    });
  }
}
SPECIMENS.sort((a, b) => a.taskId.localeCompare(b.taskId));
