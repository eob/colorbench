import type { ColorSpecimenConfig } from "./types.ts";

const choice =
  ' Return only a JSON object with one key, "choice", whose value is the selected option letter.';
export const PROMPTS: Record<string, string> = {
  matching:
    "Which swatch, A, B, C, or D, has the same flat fill color as reference R? Compare the colored interiors, not labels or borders." +
    choice,
  "lightness-lighter":
    "Which patch is lighter, A or B? Compare their flat interior colors on the shared neutral background." +
    choice,
  "lightness-darker":
    "Which patch is darker, A or B? Compare their flat interior colors on the shared neutral background." +
    choice,
  "chroma-more":
    "Which patch, A or B, is more colorful? The gray-to-color examples show the intended dimension: more colorful means farther from gray along that example, not lighter or darker." +
    choice,
  "chroma-less":
    "Which patch, A or B, is less colorful? The gray-to-color examples show the intended dimension: less colorful means closer to gray along that example, not lighter or darker." +
    choice,
  hue:
    "Which option, A, B, C, or D, has the same hue as reference R? Its lightness and colorfulness may differ. Compare the kind of color, not how light, dark, or gray it is." +
    choice,
  binding:
    "Which component, A, B, C, or D, has the same flat interior fill color as reference R? Ignore its neutral frame, label, and surrounding content." +
    choice,
  gradient:
    "Which strip, A, B, C, or D, has exactly the same left-to-right color progression as reference R? Match the entire visible color field, including where transitions occur, not just its set of colors." +
    choice,
  rgb: 'Estimate the flat interior color of R as gamma-encoded sRGB. Return only JSON with keys "r", "g", and "b", each a JSON integer from 0 to 255 (no decimal fractions). Do not report alpha or hex. The target is opaque; estimate its visible fill, not its surroundings.',
  hsl: 'Estimate the flat interior color of R in HSL derived from gamma-encoded sRGB. Return only JSON with numeric keys "h" (hue in degrees, 0 inclusive to 360 exclusive), "s" (saturation percent, 0–100), and "l" (lightness percent, 0–100). Use h=0 for an achromatic gray. The target is opaque; estimate its visible fill, not its surroundings.',
  oklch:
    'Estimate the flat interior color of R in OKLCH using the D65 white point. Return only JSON with numeric keys "l" (lightness, 0–1), "c" (nonnegative chroma in OKLCH units, not percent), and "h" (hue in degrees, 0 inclusive to 360 exclusive). Use h=0 for an achromatic gray. The target is opaque; estimate its visible fill, not its surroundings.',
};
export function getPrompt(specimen: Pick<ColorSpecimenConfig, "family" | "design">): string {
  const key = ["lightness", "chroma"].includes(specimen.family)
    ? `${specimen.family}-${specimen.design.direction}`
    : specimen.family;
  const prompt = PROMPTS[key];
  if (!prompt) throw new Error(`Missing canonical prompt: ${key}`);
  return prompt;
}
