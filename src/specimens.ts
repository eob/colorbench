import type { ColorSpecimenConfig, SemanticRole, SurfaceRole, ContrastTier, FillType, ColorTheme } from "./types.ts";

export const SPECIMENS: ColorSpecimenConfig[] = [];

let counter = 1;

function addSpecimen(item: Omit<ColorSpecimenConfig, "id">) {
  const id = `colorbench-${String(counter).padStart(3, "0")}`;
  SPECIMENS.push({ id, ...item });
  counter++;
}

// 1. SEMANTIC ROLES ACROSS LIGHT MODE
const semanticLightSolid = [
  { role: "primary" as SemanticRole, bg: "#2563eb", text: "#ffffff", tier: "aa-standard" as ContrastTier, title: "Primary Solid Action", tag: "Primary" },
  { role: "secondary" as SemanticRole, bg: "#e2e8f0", text: "#0f172a", tier: "aaa-high" as ContrastTier, title: "Secondary Neutral Chip", tag: "Secondary" },
  { role: "success" as SemanticRole, bg: "#16a34a", text: "#ffffff", tier: "aa-standard" as ContrastTier, title: "Success Verified Pill", tag: "Success" },
  { role: "warning" as SemanticRole, bg: "#d97706", text: "#ffffff", tier: "aa-standard" as ContrastTier, title: "Warning Alert Banner", tag: "Warning" },
  { role: "danger" as SemanticRole, bg: "#dc2626", text: "#ffffff", tier: "aa-standard" as ContrastTier, title: "Danger Destructive Modal", tag: "Danger" },
  { role: "info" as SemanticRole, bg: "#0284c7", text: "#ffffff", tier: "aa-standard" as ContrastTier, title: "Info Notice Callout", tag: "Info" },
];

for (const s of semanticLightSolid) {
  addSpecimen({
    semantic_role: s.role,
    surface_role: "brand-fill",
    contrast_tier: s.tier,
    fill_type: "solid",
    theme: "light",
    title: s.title,
    subtitle: `Semantic ${s.role} solid fill in light theme`,
    tag: s.tag,
    bg_color: s.bg,
    text_color: s.text,
  });
}

// 2. SEMANTIC ROLES ACROSS DARK MODE
const semanticDarkSolid = [
  { role: "primary" as SemanticRole, bg: "#3b82f6", text: "#ffffff", tier: "aa-standard" as ContrastTier, title: "Dark Primary Button", tag: "Primary" },
  { role: "secondary" as SemanticRole, bg: "#334155", text: "#f8fafc", tier: "aaa-high" as ContrastTier, title: "Dark Secondary Pill", tag: "Secondary" },
  { role: "success" as SemanticRole, bg: "#22c55e", text: "#052e16", tier: "aaa-high" as ContrastTier, title: "Dark Success Badge", tag: "Success" },
  { role: "warning" as SemanticRole, bg: "#f59e0b", text: "#451a03", tier: "aaa-high" as ContrastTier, title: "Dark Warning Card", tag: "Warning" },
  { role: "danger" as SemanticRole, bg: "#ef4444", text: "#ffffff", tier: "aa-standard" as ContrastTier, title: "Dark Danger Button", tag: "Danger" },
  { role: "info" as SemanticRole, bg: "#38bdf8", text: "#082f49", tier: "aaa-high" as ContrastTier, title: "Dark Info Toast", tag: "Info" },
];

for (const s of semanticDarkSolid) {
  addSpecimen({
    semantic_role: s.role,
    surface_role: "brand-fill",
    contrast_tier: s.tier,
    fill_type: "solid",
    theme: "dark",
    title: s.title,
    subtitle: `Semantic ${s.role} solid fill in dark theme`,
    tag: s.tag,
    bg_color: s.bg,
    text_color: s.text,
  });
}

// 3. SUBTLE TINT SURFACES
const subtleTintList = [
  { role: "primary" as SemanticRole, theme: "light" as ColorTheme, bg: "#eff6ff", text: "#1d4ed8", border: "#bfdbfe", tier: "aa-standard" as ContrastTier, title: "Primary Subtle Wash" },
  { role: "success" as SemanticRole, theme: "light" as ColorTheme, bg: "#f0fdf4", text: "#15803d", border: "#bbf7d0", tier: "aa-standard" as ContrastTier, title: "Success Subtle Wash" },
  { role: "warning" as SemanticRole, theme: "light" as ColorTheme, bg: "#fffbeb", text: "#b45309", border: "#fde68a", tier: "aa-standard" as ContrastTier, title: "Warning Subtle Wash" },
  { role: "danger" as SemanticRole, theme: "light" as ColorTheme, bg: "#fef2f2", text: "#b91c1c", border: "#fecaca", tier: "aa-standard" as ContrastTier, title: "Danger Subtle Wash" },
  { role: "info" as SemanticRole, theme: "light" as ColorTheme, bg: "#f0f9ff", text: "#0369a1", border: "#bae6fd", tier: "aa-standard" as ContrastTier, title: "Info Subtle Wash" },
  { role: "primary" as SemanticRole, theme: "dark" as ColorTheme, bg: "#172554", text: "#93c5fd", border: "#1e40af", tier: "aa-standard" as ContrastTier, title: "Dark Primary Tint" },
  { role: "success" as SemanticRole, theme: "dark" as ColorTheme, bg: "#052e16", text: "#86efac", border: "#166534", tier: "aaa-high" as ContrastTier, title: "Dark Success Tint" },
  { role: "warning" as SemanticRole, theme: "dark" as ColorTheme, bg: "#451a03", text: "#fde047", border: "#854d0e", tier: "aaa-high" as ContrastTier, title: "Dark Warning Tint" },
  { role: "danger" as SemanticRole, theme: "dark" as ColorTheme, bg: "#450a0a", text: "#fca5a5", border: "#991b1b", tier: "aa-standard" as ContrastTier, title: "Dark Danger Tint" },
  { role: "info" as SemanticRole, theme: "dark" as ColorTheme, bg: "#082f49", text: "#7dd3fc", border: "#075985", tier: "aa-standard" as ContrastTier, title: "Dark Info Tint" },
];

for (const s of subtleTintList) {
  addSpecimen({
    semantic_role: s.role,
    surface_role: "subtle-tint",
    contrast_tier: s.tier,
    fill_type: "solid",
    theme: s.theme,
    title: s.title,
    subtitle: `${s.role} tinted surface with matched border & text`,
    tag: `${s.role.toUpperCase()}-TINT`,
    bg_color: s.bg,
    text_color: s.text,
    border_color: s.border,
  });
}

// 4. OUTLINE SURFACES
const outlineList = [
  { role: "primary" as SemanticRole, theme: "light" as ColorTheme, text: "#2563eb", border: "#2563eb", tier: "aa-standard" as ContrastTier, title: "Outline Primary Button" },
  { role: "secondary" as SemanticRole, theme: "light" as ColorTheme, text: "#475569", border: "#cbd5e1", tier: "aa-standard" as ContrastTier, title: "Outline Secondary Button" },
  { role: "success" as SemanticRole, theme: "light" as ColorTheme, text: "#16a34a", border: "#16a34a", tier: "aa-standard" as ContrastTier, title: "Outline Success Button" },
  { role: "danger" as SemanticRole, theme: "light" as ColorTheme, text: "#dc2626", border: "#dc2626", tier: "aa-standard" as ContrastTier, title: "Outline Danger Button" },
  { role: "primary" as SemanticRole, theme: "dark" as ColorTheme, text: "#60a5fa", border: "#3b82f6", tier: "aa-standard" as ContrastTier, title: "Dark Outline Primary" },
  { role: "secondary" as SemanticRole, theme: "dark" as ColorTheme, text: "#94a3b8", border: "#475569", tier: "aa-standard" as ContrastTier, title: "Dark Outline Secondary" },
  { role: "success" as SemanticRole, theme: "dark" as ColorTheme, text: "#4ade80", border: "#22c55e", tier: "aaa-high" as ContrastTier, title: "Dark Outline Success" },
  { role: "danger" as SemanticRole, theme: "dark" as ColorTheme, text: "#f87171", border: "#ef4444", tier: "aa-standard" as ContrastTier, title: "Dark Outline Danger" },
];

for (const s of outlineList) {
  addSpecimen({
    semantic_role: s.role,
    surface_role: "neutral-surface",
    contrast_tier: s.tier,
    fill_type: "outline-transparent",
    theme: s.theme,
    title: s.title,
    subtitle: `Ghost transparent fill with ${s.role} stroke`,
    tag: `${s.role.toUpperCase()}-OUTLINE`,
    bg_color: "transparent",
    text_color: s.text,
    border_color: s.border,
  });
}

// 5. GRADIENTS
const gradientList = [
  { role: "primary" as SemanticRole, theme: "light" as ColorTheme, grad: "linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)", text: "#ffffff", tier: "aa-standard" as ContrastTier, title: "Primary Indigo Gradient" },
  { role: "success" as SemanticRole, theme: "light" as ColorTheme, grad: "linear-gradient(135deg, #059669 0%, #10b981 100%)", text: "#ffffff", tier: "aa-standard" as ContrastTier, title: "Emerald Vibrant Gradient" },
  { role: "warning" as SemanticRole, theme: "light" as ColorTheme, grad: "linear-gradient(135deg, #d97706 0%, #f59e0b 100%)", text: "#ffffff", tier: "large-text-subdued" as ContrastTier, title: "Amber Sunset Gradient" },
  { role: "danger" as SemanticRole, theme: "light" as ColorTheme, grad: "linear-gradient(135deg, #dc2626 0%, #e11d48 100%)", text: "#ffffff", tier: "aa-standard" as ContrastTier, title: "Crimson Blaze Gradient" },
  { role: "info" as SemanticRole, theme: "light" as ColorTheme, grad: "linear-gradient(135deg, #0284c7 0%, #06b6d4 100%)", text: "#ffffff", tier: "aa-standard" as ContrastTier, title: "Cyan Ocean Gradient" },
  { role: "primary" as SemanticRole, theme: "dark" as ColorTheme, grad: "linear-gradient(135deg, #1e3a8a 0%, #4338ca 100%)", text: "#e0e7ff", tier: "aaa-high" as ContrastTier, title: "Dark Indigo Flow" },
  { role: "danger" as SemanticRole, theme: "dark" as ColorTheme, grad: "linear-gradient(135deg, #881337 0%, #991b1b 100%)", text: "#fecdd3", tier: "aaa-high" as ContrastTier, title: "Dark Ruby Flow" },
  { role: "secondary" as SemanticRole, theme: "dark" as ColorTheme, grad: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)", text: "#f8fafc", tier: "aaa-high" as ContrastTier, title: "Dark Slate Shimmer" },
];

for (const s of gradientList) {
  addSpecimen({
    semantic_role: s.role,
    surface_role: "brand-fill",
    contrast_tier: s.tier,
    fill_type: "linear-gradient",
    theme: s.theme,
    title: s.title,
    subtitle: `Directional 135deg linear gradient with ${s.role} palette`,
    tag: `${s.role.toUpperCase()}-GRAD`,
    bg_color: s.grad,
    text_color: s.text,
    gradient_css: s.grad,
  });
}

// 6. CONTRAST DISCRIMINATION
const contrastTests = [
  { tier: "aaa-high" as ContrastTier, bg: "#ffffff", text: "#000000", theme: "light" as ColorTheme, title: "AAA Stark High Contrast (21:1)", role: "secondary" as SemanticRole },
  { tier: "aaa-high" as ContrastTier, bg: "#0f172a", text: "#ffffff", theme: "dark" as ColorTheme, title: "Dark AAA Stark High Contrast (18:1)", role: "secondary" as SemanticRole },
  { tier: "aaa-high" as ContrastTier, bg: "#1e1b4b", text: "#c7d2fe", theme: "dark" as ColorTheme, title: "Dark Violet AAA Contrast (9.2:1)", role: "primary" as SemanticRole },
  { tier: "aaa-high" as ContrastTier, bg: "#022c22", text: "#a7f3d0", theme: "dark" as ColorTheme, title: "Dark Forest AAA Contrast (11.5:1)", role: "success" as SemanticRole },
  { tier: "aa-standard" as ContrastTier, bg: "#ffffff", text: "#475569", theme: "light" as ColorTheme, title: "AA Standard Slate Text (5.4:1)", role: "secondary" as SemanticRole },
  { tier: "aa-standard" as ContrastTier, bg: "#ffffff", text: "#2563eb", theme: "light" as ColorTheme, title: "AA Standard Blue Link (4.6:1)", role: "primary" as SemanticRole },
  { tier: "aa-standard" as ContrastTier, bg: "#18181b", text: "#a1a1aa", theme: "dark" as ColorTheme, title: "Dark AA Standard Text (5.1:1)", role: "secondary" as SemanticRole },
  { tier: "large-text-subdued" as ContrastTier, bg: "#ffffff", text: "#94a3b8", theme: "light" as ColorTheme, title: "Subdued Muted Label (3.3:1)", role: "secondary" as SemanticRole },
  { tier: "large-text-subdued" as ContrastTier, bg: "#f8fafc", text: "#38bdf8", theme: "light" as ColorTheme, title: "Subdued Sky Text on White (3.1:1)", role: "info" as SemanticRole },
  { tier: "large-text-subdued" as ContrastTier, bg: "#090d16", text: "#64748b", theme: "dark" as ColorTheme, title: "Dark Subdued Secondary (3.4:1)", role: "secondary" as SemanticRole },
  { tier: "failing-disabled" as ContrastTier, bg: "#ffffff", text: "#cbd5e1", theme: "light" as ColorTheme, title: "Failing Low-Contrast Text (1.6:1)", role: "secondary" as SemanticRole },
  { tier: "failing-disabled" as ContrastTier, bg: "#f1f5f9", text: "#94a3b8", theme: "light" as ColorTheme, title: "Disabled Input Ghost Text (2.4:1)", role: "secondary" as SemanticRole },
  { tier: "failing-disabled" as ContrastTier, bg: "#1e293b", text: "#475569", theme: "dark" as ColorTheme, title: "Dark Disabled Button (2.1:1)", role: "secondary" as SemanticRole },
  { tier: "failing-disabled" as ContrastTier, bg: "#2563eb", text: "#60a5fa", theme: "light" as ColorTheme, title: "Low-Contrast Tone-on-Tone (2.2:1)", role: "primary" as SemanticRole },
];

for (const c of contrastTests) {
  addSpecimen({
    semantic_role: c.role,
    surface_role: "neutral-surface",
    contrast_tier: c.tier,
    fill_type: "solid",
    theme: c.theme,
    title: c.title,
    subtitle: `Contrast ratio threshold verification: ${c.tier}`,
    tag: `CONTRAST-${c.tier.toUpperCase()}`,
    bg_color: c.bg,
    text_color: c.text,
  });
}

// 7. ELEVATED SURFACES
const surfaceTiers = [
  { surf: "neutral-surface" as SurfaceRole, bg: "#090d16", text: "#f8fafc", title: "Base Canvas Surface-0", theme: "dark" as ColorTheme },
  { surf: "elevated-surface" as SurfaceRole, bg: "#131b2e", text: "#f8fafc", title: "Elevated Card Surface-1", theme: "dark" as ColorTheme },
  { surf: "elevated-surface" as SurfaceRole, bg: "#1e293b", text: "#f8fafc", title: "Elevated Dialog Surface-2", theme: "dark" as ColorTheme },
  { surf: "elevated-surface" as SurfaceRole, bg: "#334155", text: "#ffffff", title: "Elevated Popover Surface-3", theme: "dark" as ColorTheme },
  { surf: "neutral-surface" as SurfaceRole, bg: "#ffffff", text: "#0f172a", title: "Light Neutral Surface-0", theme: "light" as ColorTheme },
  { surf: "subtle-tint" as SurfaceRole, bg: "#f8fafc", text: "#0f172a", title: "Light Off-White Surface-1", theme: "light" as ColorTheme },
  { surf: "subtle-tint" as SurfaceRole, bg: "#f1f5f9", text: "#0f172a", title: "Light Slate Well Surface-2", theme: "light" as ColorTheme },
];

for (const st of surfaceTiers) {
  addSpecimen({
    semantic_role: "secondary",
    surface_role: st.surf,
    contrast_tier: "aaa-high",
    fill_type: "solid",
    theme: st.theme,
    title: st.title,
    subtitle: `Layered surface elevation step (${st.surf})`,
    tag: `SURFACE-${st.surf.toUpperCase()}`,
    bg_color: st.bg,
    text_color: st.text,
  });
}

// 8. ARCHETYPES
const uiArchetypes = [
  { role: "primary" as SemanticRole, fill: "solid" as FillType, bg: "#3b82f6", text: "#ffffff", tier: "aa-standard" as ContrastTier, theme: "light" as ColorTheme, title: "Active Beta Pill" },
  { role: "success" as SemanticRole, fill: "outline-transparent" as FillType, bg: "transparent", text: "#16a34a", border: "#86efac", tier: "aa-standard" as ContrastTier, theme: "light" as ColorTheme, title: "Operational 99.9% Badge" },
  { role: "warning" as SemanticRole, fill: "solid" as FillType, bg: "#fef3c7", text: "#92400e", border: "#fde68a", tier: "aaa-high" as ContrastTier, theme: "light" as ColorTheme, title: "Plan Expiring Pill" },
  { role: "danger" as SemanticRole, fill: "solid" as FillType, bg: "#fee2e2", text: "#991b1b", border: "#fecaca", tier: "aaa-high" as ContrastTier, theme: "light" as ColorTheme, title: "Build Failed Badge" },
  { role: "info" as SemanticRole, fill: "solid" as FillType, bg: "#e0f2fe", text: "#075985", border: "#bae6fd", tier: "aaa-high" as ContrastTier, theme: "light" as ColorTheme, title: "New Feature Tag" },
  { role: "primary" as SemanticRole, fill: "solid" as FillType, bg: "#1e3a8a", text: "#bfdbfe", tier: "aaa-high" as ContrastTier, theme: "dark" as ColorTheme, title: "Dark Pro Tier Pill" },
  { role: "success" as SemanticRole, fill: "solid" as FillType, bg: "#064e3b", text: "#6ee7b7", tier: "aaa-high" as ContrastTier, theme: "dark" as ColorTheme, title: "Dark Verified Account" },
  { role: "danger" as SemanticRole, fill: "solid" as FillType, bg: "#7f1d1d", text: "#fca5a5", tier: "aaa-high" as ContrastTier, theme: "dark" as ColorTheme, title: "Dark Incident Alert" },
  { role: "warning" as SemanticRole, fill: "solid" as FillType, bg: "#78350f", text: "#fde68a", tier: "aaa-high" as ContrastTier, theme: "dark" as ColorTheme, title: "Dark High CPU Usage" },
];

for (const a of uiArchetypes) {
  addSpecimen({
    semantic_role: a.role,
    surface_role: a.fill === "solid" ? "brand-fill" : "neutral-surface",
    contrast_tier: a.tier,
    fill_type: a.fill,
    theme: a.theme,
    title: a.title,
    subtitle: `Production component archetype: ${a.title}`,
    tag: `ARCHETYPE-${a.role.toUpperCase()}`,
    bg_color: a.bg,
    text_color: a.text,
    border_color: a.border,
  });
}

// 9. SYSTEMATIC HUE PALETTE SWEEPS
const remainingHues = [
  { role: "primary" as SemanticRole, bg: "#4f46e5", text: "#ffffff", title: "Indigo Core Primary" },
  { role: "primary" as SemanticRole, bg: "#6366f1", text: "#ffffff", title: "Iris Active Action" },
  { role: "primary" as SemanticRole, bg: "#7c3aed", text: "#ffffff", title: "Violet Brand Action" },
  { role: "primary" as SemanticRole, bg: "#8b5cf6", text: "#ffffff", title: "Purple Action Button" },
  { role: "success" as SemanticRole, bg: "#059669", text: "#ffffff", title: "Emerald Core Success" },
  { role: "success" as SemanticRole, bg: "#10b981", text: "#064e3b", title: "Teal Green Success" },
  { role: "success" as SemanticRole, bg: "#14b8a6", text: "#042f2e", title: "Teal Verified Status" },
  { role: "warning" as SemanticRole, bg: "#ea580c", text: "#ffffff", title: "Orange Amber Warning" },
  { role: "warning" as SemanticRole, bg: "#f97316", text: "#ffffff", title: "Tangerine Caution Tag" },
  { role: "warning" as SemanticRole, bg: "#eab308", text: "#422006", title: "Yellow Warning Notice" },
  { role: "danger" as SemanticRole, bg: "#b91c1c", text: "#ffffff", title: "Deep Red Danger State" },
  { role: "danger" as SemanticRole, bg: "#e11d48", text: "#ffffff", title: "Rose Destructive Button" },
  { role: "danger" as SemanticRole, bg: "#f43f5e", text: "#ffffff", title: "Coral Warning Alert" },
  { role: "info" as SemanticRole, bg: "#0891b2", text: "#ffffff", title: "Deep Cyan Info Chip" },
  { role: "info" as SemanticRole, bg: "#06b6d4", text: "#164e63", title: "Sky Blue Info Callout" },
];

for (const rh of remainingHues) {
  for (const theme of ["light", "dark"] as ColorTheme[]) {
    if (SPECIMENS.length >= 100) break;
    addSpecimen({
      semantic_role: rh.role,
      surface_role: "brand-fill",
      contrast_tier: "aa-standard",
      fill_type: "solid",
      theme,
      title: `${rh.title} (${theme})`,
      subtitle: `Systematic hue palette sweep: ${rh.role} in ${theme} mode`,
      tag: `HUE-${rh.role.toUpperCase()}`,
      bg_color: rh.bg,
      text_color: rh.text,
    });
  }
}

while (SPECIMENS.length < 100) {
  const i = SPECIMENS.length;
  addSpecimen({
    semantic_role: "secondary",
    surface_role: "neutral-surface",
    contrast_tier: "aaa-high",
    fill_type: "solid",
    theme: i % 2 === 0 ? "light" : "dark",
    title: `Neutral Reference Surface ${i + 1}`,
    subtitle: `Reference baseline card ${i + 1}`,
    tag: "BASELINE",
    bg_color: i % 2 === 0 ? "#ffffff" : "#111827",
    text_color: i % 2 === 0 ? "#0f172a" : "#f9fafb",
  });
}
