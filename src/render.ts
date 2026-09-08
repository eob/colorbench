import { chromium } from "playwright";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { SPECIMENS } from "./specimens.ts";
import type { ColorBenchmarkManifestItem, ColorSpecimenConfig } from "./types.ts";

function buildCardHtml(s: ColorSpecimenConfig): string {
  const canvasBg = s.theme === "dark" ? "#090d16" : "#f1f5f9";
  const cardBorder = s.border_color ? `border: 2px solid ${s.border_color};` : (s.theme === "dark" ? "border: 1px solid rgba(255,255,255,0.1);" : "border: 1px solid rgba(0,0,0,0.08);");
  const bgStyle = s.gradient_css ? `background: ${s.gradient_css};` : (s.fill_type === "outline-transparent" ? "background: transparent;" : `background-color: ${s.bg_color};`);

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 560px;
    height: 380px;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: ${canvasBg};
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  .card {
    width: 440px;
    height: 250px;
    border-radius: 14px;
    padding: 28px 32px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    ${bgStyle}
    ${cardBorder}
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    color: ${s.text_color};
  }
  .header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .badge {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 4px 10px;
    border-radius: 6px;
    border: 1px solid currentColor;
    opacity: 0.9;
  }
  .title {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.01em;
    line-height: 1.25;
    margin-top: 14px;
  }
  .subtitle {
    font-size: 14px;
    font-weight: 400;
    line-height: 1.4;
    opacity: 0.85;
    margin-top: 6px;
  }
  .footer-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 14px;
    border-top: 1px solid currentColor;
    opacity: 0.85;
    font-size: 12px;
    font-weight: 600;
  }
</style>
</head>
<body>
  <div class="card">
    <div>
      <div class="header-row">
        <span class="badge">${s.tag}</span>
        <span style="font-size: 12px; opacity: 0.75;">${s.theme.toUpperCase()}</span>
      </div>
      <h2 class="title">${s.title}</h2>
      <p class="subtitle">${s.subtitle}</p>
    </div>
    <div class="footer-row">
      <span>ROLE: ${s.semantic_role.toUpperCase()}</span>
      <span>TIER: ${s.contrast_tier.toUpperCase()}</span>
    </div>
  </div>
</body>
</html>`;
}

async function renderDataset() {
  const renderedDir = join(process.cwd(), "dataset", "rendered");
  const manifestDir = join(process.cwd(), "dataset", "colorbench-1");
  await mkdir(renderedDir, { recursive: true });
  await mkdir(manifestDir, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 560, height: 380 },
    deviceScaleFactor: 2,
  });
  const page = await context.newPage();

  const manifestItems: ColorBenchmarkManifestItem[] = [];

  console.log(`Rendering ${SPECIMENS.length} specimens at 2x DPR...`);

  for (let i = 0; i < SPECIMENS.length; i++) {
    const s = SPECIMENS[i];
    const filename = `${s.id}.png`;
    const imagePath = join(renderedDir, filename);

    const html = buildCardHtml(s);
    await page.setContent(html, { waitUntil: "networkidle" });
    await page.screenshot({ path: imagePath, type: "png" });

    manifestItems.push({
      taskId: s.id,
      imagePath,
      imageFilename: filename,
      groundTruth: {
        semantic_role: s.semantic_role,
        surface_role: s.surface_role,
        contrast_tier: s.contrast_tier,
        fill_type: s.fill_type,
        theme: s.theme,
        bg_color: s.bg_color,
        text_color: s.text_color,
      },
      prompt: `Analyze the visual color design and contrast of the card container in this software screenshot. Output a JSON object with:
- semantic_role: "primary" | "secondary" | "success" | "warning" | "danger" | "info"
- surface_role: "neutral-surface" | "subtle-tint" | "brand-fill" | "elevated-surface"
- contrast_tier: "aaa-high" | "aa-standard" | "large-text-subdued" | "failing-disabled"
- fill_type: "solid" | "linear-gradient" | "outline-transparent"
- theme: "light" | "dark"`,
    });

    if ((i + 1) % 20 === 0 || i === SPECIMENS.length - 1) {
      console.log(`  Rendered ${i + 1}/${SPECIMENS.length} screenshots`);
    }
  }

  await browser.close();

  const manifestFile = join(manifestDir, "manifest.json");
  await writeFile(manifestFile, JSON.stringify(manifestItems, null, 2), "utf-8");
  console.log(`Wrote manifest with ${manifestItems.length} tasks to ${manifestFile}`);
}

renderDataset().catch((err) => {
  console.error(err);
  process.exit(1);
});
