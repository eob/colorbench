import { chromium, type Page } from "playwright";
import * as fs from "node:fs";
import * as path from "node:path";
import { createHash } from "node:crypto";
import { hueDistance, rgbToOklch } from "./colors.ts";
import { getPrompt, PROMPTS } from "./prompts.ts";
import { REPOSITORY, resolveCandidateOutput } from "./output.ts";
import { CONTEXT_SURROUNDS, SPECIMENS } from "./specimens.ts";
import type {
  Choice,
  ColorBenchmarkManifestItem,
  ColorField,
  ColorSpecimenConfig,
  PixelRegion,
  RenderedEvidence,
  Rgb,
} from "./types.ts";

export const VIEWPORT = { width: 800, height: 640, deviceScaleFactor: 1 };
export const FONT_PATH = new URL("./assets/DejaVuSans.ttf", import.meta.url);
const FONT_BYTES = fs.readFileSync(FONT_PATH);
export const sha256 = (bytes: Uint8Array | string) =>
  createHash("sha256").update(bytes).digest("hex");
export const FONT_SHA256 = sha256(FONT_BYTES);
interface PlacedField extends ColorField {
  role: PixelRegion["role"];
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  canvasX: number;
  canvasY: number;
  canvasWidth: number;
  canvasHeight: number;
  ring?: { color: Rgb; width: number };
  interior?: Rgb;
}
const PAGE_BACKGROUND: Rgb = [238, 238, 238];
export function placeFields(s: ColorSpecimenConfig): PlacedField[] {
  const fields: PlacedField[] = [];
  const numeric = ["rgb", "hsl", "oklch"].includes(s.family);
  const gradient = s.family === "gradient";
  const dot = s.family === "smallmatch" && s.design.layout === "dot";
  const frame = s.family === "smallmatch" && s.design.layout === "frame";
  const context = s.family === "context";
  const push = (
    color: ColorField,
    role: PixelRegion["role"],
    id: string,
    x: number,
    y: number,
    width: number,
    height: number,
    extra?: {
      canvasX?: number;
      canvasY?: number;
      canvasWidth?: number;
      canvasHeight?: number;
      ring?: { color: Rgb; width: number };
      interior?: Rgb;
    },
  ) => {
    fields.push({
      ...color,
      role,
      id,
      x,
      y,
      width,
      height,
      canvasX: extra?.canvasX ?? x,
      canvasY: extra?.canvasY ?? y,
      canvasWidth: extra?.canvasWidth ?? width,
      canvasHeight: extra?.canvasHeight ?? height,
      ...(extra?.ring ? { ring: extra.ring } : {}),
      ...(extra?.interior ? { interior: extra.interior } : {}),
    });
  };
  if (s.target) {
    if (numeric) push(s.target, "target", "R", 320, 210, 160, 160);
    else if (gradient) push(s.target, "target", "R", 280, 135, 240, 60);
    else if (dot) push(s.target, "target", "R", 390, 140, 20, 20);
    else if (frame)
      push(s.target, "target", "R", 358, 140, 84, 84, {
        ring: { color: s.target.rgb!, width: 3 },
        interior: PAGE_BACKGROUND,
      });
    else push(s.target, "target", "R", 358, 140, 84, 84);
  }
  for (const [i, option] of s.options.entries()) {
    const pair = s.options.length === 2;
    const id = "ABCD"[i]!;
    if (gradient) push(option, "option", id, [80, 480][i % 2]!, [300, 465][Math.floor(i / 2)]!, 240, 60);
    else if (dot) push(option, "option", id, [128, 302, 476, 650][i]!, 392, 20, 20);
    else if (frame)
      push(option, "option", id, [96, 270, 444, 618][i]!, 360, 84, 84, {
        ring: { color: option.rgb!, width: 3 },
        interior: PAGE_BACKGROUND,
      });
    else if (context) {
      const canvasX = [84, 258, 432, 606][i]!;
      push(option, "option", id, canvasX + 12, 360, 84, 84, {
        canvasX,
        canvasY: 348,
        canvasWidth: 108,
        canvasHeight: 108,
        ring: { color: CONTEXT_SURROUNDS[i]!, width: 12 },
      });
    } else if (pair) push(option, "option", id, [220, 496][i]!, 330, 84, 84);
    else push(option, "option", id, [96, 270, 444, 618][i]!, 360, 84, 84);
  }
  const referenceColors = s.design.reference?.colors as Rgb[] | undefined;
  for (const [i, rgb] of (referenceColors ?? []).entries())
    push({ rgb }, "reference", `example-${i}`, 160 + i * 96, 155, 64, 28);
  return fields;
}
function imageQuestion(s: ColorSpecimenConfig): string {
  switch (s.family) {
    case "matching":
      return "Which swatch has the same color as R?";
    case "binding":
      return "Which component has the same interior fill color as R?";
    case "hue":
      return "Which option has R’s hue? Lightness and colorfulness may differ.";
    case "lightness":
      return `Which patch is ${s.design.direction}, A or B?`;
    case "chroma":
      return `Which patch is ${s.design.direction} colorful, A or B?`;
    case "gradient":
      return "Which strip has exactly R’s left-to-right color progression?";
    case "samediff":
      return "Are A and B the same color?";
    case "context":
      return "Which interior matches R? Ignore the surrounds.";
    case "smallmatch":
      return "Which small swatch matches R?";
    default:
      return "Estimate the interior color of R in the requested format.";
  }
}
export function generateHtml(s: ColorSpecimenConfig): string {
  const fields = placeFields(s);
  const shapes = fields
    .map((field) => {
      const label =
        field.role === "reference"
          ? ""
          : `<div class="label" style="left:${field.canvasX}px;top:${field.canvasY - 30}px;width:${field.canvasWidth}px">${field.id}</div>`;
      const frame =
        s.family === "binding" && field.role === "option"
          ? `<div class="component" style="left:${field.x - 20}px;top:${field.y - 50}px"><div class="line"></div><div class="line bottom"></div></div>`
          : "";
      return `${frame}${label}<canvas data-region="${field.id}" width="${field.canvasWidth}" height="${field.canvasHeight}" style="left:${field.canvasX}px;top:${field.canvasY}px"></canvas>`;
    })
    .join("");
  const explanation =
    s.family === "chroma"
      ? "Dimension reference: gray → colorful"
      : s.family === "lightness"
        ? "Dimension reference: dark → light"
        : "";
  const footer =
    s.family === "smallmatch" && s.design.layout === "frame"
      ? "Compare the colored outlines. Labels and neutral areas are not part of the color."
      : "Compare the colored interiors. Labels and neutral frames are not part of the color.";
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><style>
  @font-face{font-family:ColorBench;src:url(data:font/ttf;base64,${FONT_BYTES.toString("base64")}) format("truetype");font-weight:400;font-style:normal}
  *{box-sizing:border-box}html,body{margin:0;width:800px;height:640px;background:rgb(238,238,238);overflow:hidden}
  body{position:relative;color:#202020;font-family:ColorBench;font-size:16px;line-height:24px;font-synthesis:none}
  #question{position:absolute;left:40px;top:28px;width:720px;text-align:center;margin:0;font-size:16px;font-weight:400}
  .label{position:absolute;text-align:center;height:24px}canvas{position:absolute;display:block}
  .explanation{position:absolute;left:40px;top:108px;width:720px;text-align:center}
  .component{position:absolute;width:124px;height:170px;border:1px solid #aaa;border-radius:8px;background:rgb(238,238,238)}
  .line{position:absolute;left:15px;top:12px;width:92px;height:3px;background:#aaa}.line.bottom{top:149px;width:62px}
  .footer{position:absolute;left:40px;bottom:28px;width:720px;text-align:center;color:#555}
  </style></head><body><h1 id="question">${imageQuestion(s)}</h1>
  ${explanation ? `<div class="explanation">${explanation}</div>` : ""}${shapes}
  <div class="footer">${footer}</div>
  <script>(()=>{const fields=${JSON.stringify(fields)};for(const f of fields){const canvas=document.querySelector('[data-region="'+f.id+'"]');const ctx=canvas.getContext('2d',{colorSpace:'srgb'});const img=ctx.createImageData(f.canvasWidth,f.canvasHeight);for(let y=0;y<f.canvasHeight;y++)for(let x=0;x<f.canvasWidth;x++){const ring=f.ring&&(x<f.ring.width||x>=f.canvasWidth-f.ring.width||y<f.ring.width||y>=f.canvasHeight-f.ring.width);const color=ring?f.ring.color:f.interior?f.interior:f.columns?f.columns[x]:f.rgb;const offset=(y*f.canvasWidth+x)*4;img.data[offset]=color[0];img.data[offset+1]=color[1];img.data[offset+2]=color[2];img.data[offset+3]=255;}ctx.putImageData(img,0,0);}})();</script>
  </body></html>`;
}
export async function inspectPixels(
  page: Page,
  screenshot: Buffer,
  fields: PlacedField[],
): Promise<PixelRegion[]> {
  const decoded = await page.evaluate(
    async ({ data, fields }) => {
      const image = new Image();
      image.src = `data:image/png;base64,${data}`;
      await image.decode();
      const canvas = document.createElement("canvas");
      canvas.width = image.width;
      canvas.height = image.height;
      const ctx = canvas.getContext("2d", { colorSpace: "srgb" })!;
      ctx.drawImage(image, 0, 0);
      return fields.map((field) => {
        const rgba = ctx.getImageData(field.x, field.y, field.width, field.height).data;
        const rgb = new Uint8Array(field.width * field.height * 3);
        for (let i = 0, j = 0; i < rgba.length; i += 4) {
          if (rgba[i + 3] !== 255) throw new Error("Nonopaque color region");
          rgb[j++] = rgba[i]!;
          rgb[j++] = rgba[i + 1]!;
          rgb[j++] = rgba[i + 2]!;
        }
        const parts: string[] = [];
        for (let i = 0; i < rgb.length; i += 16384)
          parts.push(String.fromCharCode(...rgb.subarray(i, i + 16384)));
        return {
          rgb: [rgb[0], rgb[1], rgb[2]],
          uniform: rgb.every((v, i) => v === rgb[i % 3]),
          bytes: btoa(parts.join("")),
        };
      });
    },
    { data: screenshot.toString("base64"), fields },
  );
  return fields.map((field, i) => {
    const actual = decoded[i]!;
    if (field.rgb && !field.interior && (!actual.uniform || JSON.stringify(field.rgb) !== JSON.stringify(actual.rgb)))
      throw new Error(`Decoded flat pixels differ for ${field.id}`);
    return {
      role: field.role,
      id: field.id,
      x: field.x,
      y: field.y,
      width: field.width,
      height: field.height,
      ...(actual.uniform ? { rgb: actual.rgb as Rgb } : {}),
      pixelSha256: sha256(Buffer.from(actual.bytes, "base64")),
    };
  });
}
export function groundTruthFromPixels(
  s: ColorSpecimenConfig,
  regions: PixelRegion[],
): ColorBenchmarkManifestItem["groundTruth"] {
  const target = regions.find((r) => r.role === "target");
  const options = regions.filter((r) => r.role === "option");
  if (["rgb", "hsl", "oklch"].includes(s.family)) {
    if (!target?.rgb) throw new Error("Numeric target must have a uniform decoded interior");
    return { rgb: target.rgb };
  }
  let selected: PixelRegion | undefined;
  if (["matching", "binding", "gradient", "context", "smallmatch"].includes(s.family)) {
    const matches = options.filter((r) => r.pixelSha256 === target?.pixelSha256);
    if (matches.length !== 1) throw new Error("Exactly one decoded option must match the target");
    selected = matches[0];
  } else if (s.family === "samediff") {
    const a = options.find((r) => r.id === "A")!;
    const b = options.find((r) => r.id === "B")!;
    const equal = a.pixelSha256 === b.pixelSha256;
    if (equal !== s.design.same) throw new Error("Decoded same-different equality differs");
    const sameChoice = s.design.direction === "sameA" ? "A" : "B";
    const choice = equal ? sameChoice : sameChoice === "A" ? "B" : "A";
    if (choice !== s.answer) throw new Error(`Decoded ground truth differs for ${s.taskId}`);
    return { choice: choice as Choice };
  } else {
    const targetColor = target?.rgb ? rgbToOklch(target.rgb) : undefined;
    if (s.family === "hue" && (!targetColor || targetColor.c < 0.02))
      throw new Error("Hue target is achromatic");
    const values = options.map((r) => {
      if (!r.rgb) throw new Error("Comparison options must be uniform");
      const value = rgbToOklch(r.rgb);
      return s.family === "lightness"
        ? value.l
        : s.family === "chroma"
          ? value.c
          : hueDistance(value.h, targetColor!.h);
    });
    const descending = s.design.direction === "lighter" || s.design.direction === "more";
    const wanted = descending ? Math.max(...values) : Math.min(...values);
    const matches = options.filter((_, i) => values[i] === wanted);
    if (matches.length !== 1) throw new Error("Comparison has no unique answer");
    selected = matches[0];
  }
  if (!selected || selected.id !== s.answer)
    throw new Error(`Decoded ground truth differs for ${s.taskId}`);
  return { choice: selected.id as Choice };
}
export async function renderDataset(requested?: string): Promise<ColorBenchmarkManifestItem[]> {
  const output = resolveCandidateOutput(requested);
  if (fs.existsSync(output)) {
    const catalog = path.join(output, "catalog.json");
    if (
      !fs.existsSync(catalog) ||
      JSON.parse(fs.readFileSync(catalog, "utf8")).artifactType !== "colorbench-pilot-candidate"
    ) {
      throw new Error("Existing candidate is not owned by this renderer; refusing replacement");
    }
  }
  fs.mkdirSync(path.dirname(output), { recursive: true });
  const staging = fs.mkdtempSync(path.join(path.dirname(output), ".colorbench-candidate-"));
  const browser = await chromium.launch({ headless: true, args: ["--force-color-profile=srgb"] });
  try {
    fs.mkdirSync(path.join(staging, "fonts"));
    fs.copyFileSync(FONT_PATH, path.join(staging, "fonts/DejaVuSans.ttf"));
    fs.copyFileSync(
      new URL("./assets/DejaVuSans.LICENSE", import.meta.url),
      path.join(staging, "fonts/DejaVuSans.LICENSE"),
    );
    const page = await browser.newPage({
      viewport: { width: VIEWPORT.width, height: VIEWPORT.height },
      deviceScaleFactor: 1,
    });
    const pageErrors: string[] = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    const cdp = await page.context().newCDPSession(page);
    await cdp.send("DOM.enable");
    await cdp.send("CSS.enable");
    const imageCache = new Map<string, { hash: string; evidence: RenderedEvidence }>();
    const manifest: ColorBenchmarkManifestItem[] = [];
    for (const s of SPECIMENS) {
      const imageFilename = `${s.imageId}.png`;
      let image = imageCache.get(s.imageId);
      if (!image) {
        await page.setContent(generateHtml(s));
        await page.evaluate(async () => {
          await document.fonts.ready;
          if (!document.fonts.check("16px ColorBench"))
            throw new Error("Reference font failed to load");
        });
        if (pageErrors.length) throw new Error(`Stimulus script failed: ${pageErrors.join("; ")}`);
        const documentNode = await cdp.send("DOM.getDocument");
        const node = await cdp.send("DOM.querySelector", {
          nodeId: documentNode.root.nodeId,
          selector: "#question",
        });
        const { fonts } = await cdp.send("CSS.getPlatformFontsForNode", { nodeId: node.nodeId });
        if (
          !fonts.length ||
          fonts.some(
            (font) =>
              font.familyName !== "DejaVu Sans" || !font.isCustomFont || font.glyphCount <= 0,
          )
        )
          throw new Error("Bundled font was not actually used");
        const screenshot = await page.screenshot({ type: "png", animations: "disabled" });
        const regions = await inspectPixels(page, screenshot, placeFields(s));
        const evidence: RenderedEvidence = {
          width: VIEWPORT.width,
          height: VIEWPORT.height,
          browserVersion: browser.version(),
          platform: process.platform,
          viewport: VIEWPORT,
          colorSpace: "srgb",
          font: {
            path: "fonts/DejaVuSans.ttf",
            sha256: FONT_SHA256,
            family: "DejaVu Sans",
            sizePx: 16,
            lineHeightPx: 24,
            platformFonts: fonts,
          },
          regions,
        };
        image = { hash: sha256(screenshot), evidence };
        fs.writeFileSync(path.join(staging, imageFilename), screenshot);
        imageCache.set(s.imageId, image);
      }
      manifest.push({
        taskId: s.taskId,
        family: s.family,
        groupId: s.groupId,
        imageFilename,
        imageSha256: image.hash,
        groundTruth: groundTruthFromPixels(s, image.evidence.regions),
        prompt: getPrompt(s),
        design: s.design,
        rendered: image.evidence,
      });
    }
    fs.writeFileSync(path.join(staging, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
    fs.writeFileSync(
      path.join(staging, "catalog.json"),
      JSON.stringify(
        {
          schemaVersion: 1,
          artifactType: "colorbench-pilot-candidate",
          version: "0.3.1",
          status: "human-pilot-pending",
          questionCount: manifest.length,
          uniqueImageCount: imageCache.size,
          promptRegistry: PROMPTS,
          font: { path: "fonts/DejaVuSans.ttf", sha256: FONT_SHA256 },
          tasks: manifest.map(({ rendered, imageSha256, prompt, ...item }) => item),
        },
        null,
        2,
      ) + "\n",
    );
    resolveCandidateOutput(requested);
    const previous = `${staging}-previous`;
    if (fs.existsSync(output)) fs.renameSync(output, previous);
    try {
      fs.renameSync(staging, output);
    } catch (error) {
      if (fs.existsSync(previous)) fs.renameSync(previous, output);
      throw error;
    }
    if (fs.existsSync(previous)) fs.rmSync(previous, { recursive: true });
    console.log(
      `Rendered ${manifest.length} questions / ${imageCache.size} unique images into ${path.relative(REPOSITORY, output)}`,
    );
    return manifest;
  } finally {
    await browser.close();
    if (fs.existsSync(staging)) fs.rmSync(staging, { recursive: true });
  }
}
if (import.meta.main) {
  const args = process.argv.slice(2);
  if (args.length && (args.length !== 2 || args[0] !== "--output-dir"))
    throw new Error("Usage: bun src/render.ts [--output-dir dataset/candidate-rendered]");
  renderDataset(args[1]).catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
