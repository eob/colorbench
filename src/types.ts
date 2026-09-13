export const FAMILIES = [
  "matching",
  "lightness",
  "chroma",
  "hue",
  "binding",
  "gradient",
  "samediff",
  "context",
  "smallmatch",
  "rgb",
  "hsl",
  "oklch",
] as const;
export type Family = (typeof FAMILIES)[number];
export type Rgb = [number, number, number];
export type Choice = "A" | "B" | "C" | "D";
export interface Oklab {
  l: number;
  a: number;
  b: number;
}
export interface Oklch {
  l: number;
  c: number;
  h: number;
}
export interface Hsl {
  h: number;
  s: number;
  l: number;
}
export interface ColorField {
  rgb?: Rgb;
  columns?: Rgb[];
}
export interface ColorSpecimenConfig {
  taskId: string;
  family: Family;
  groupId: string;
  imageId: string;
  target?: ColorField;
  options: ColorField[];
  answer?: Choice;
  design: {
    axis: string;
    difficulty: string;
    sourceRgb?: Rgb;
    direction?: "lighter" | "darker" | "more" | "less" | "sameA" | "sameB";
    reference?: Record<string, unknown>;
    [key: string]: unknown;
  };
}
export interface PixelRegion {
  role: "target" | "option" | "reference";
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  rgb?: Rgb;
  pixelSha256: string;
}
export interface RenderedEvidence {
  width: number;
  height: number;
  browserVersion: string;
  platform: string;
  viewport: { width: number; height: number; deviceScaleFactor: number };
  font: {
    path: string;
    sha256: string;
    family: string;
    sizePx: number;
    lineHeightPx: number;
    platformFonts: { familyName: string; isCustomFont: boolean; glyphCount: number }[];
  };
  colorSpace: "srgb";
  regions: PixelRegion[];
}
export interface ColorBenchmarkManifestItem {
  taskId: string;
  family: Family;
  groupId: string;
  imageFilename: string;
  imageSha256: string;
  groundTruth: { choice: Choice } | { rgb: Rgb };
  prompt: string;
  design: ColorSpecimenConfig["design"];
  rendered: RenderedEvidence;
}
