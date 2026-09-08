export type SemanticRole = "primary" | "secondary" | "success" | "warning" | "danger" | "info";
export type SurfaceRole = "neutral-surface" | "subtle-tint" | "brand-fill" | "elevated-surface";
export type ContrastTier = "aaa-high" | "aa-standard" | "large-text-subdued" | "failing-disabled";
export type FillType = "solid" | "linear-gradient" | "outline-transparent";
export type ColorTheme = "light" | "dark";

export interface ColorSpecimenConfig {
  id: string;
  semantic_role: SemanticRole;
  surface_role: SurfaceRole;
  contrast_tier: ContrastTier;
  fill_type: FillType;
  theme: ColorTheme;
  title: string;
  subtitle: string;
  tag: string;
  bg_color: string;
  text_color: string;
  border_color?: string;
  gradient_css?: string;
}

export interface ColorBenchmarkManifestItem {
  taskId: string;
  imagePath: string;
  imageFilename: string;
  groundTruth: {
    semantic_role: SemanticRole;
    surface_role: SurfaceRole;
    contrast_tier: ContrastTier;
    fill_type: FillType;
    theme: ColorTheme;
    bg_color: string;
    text_color: string;
  };
  prompt: string;
}
