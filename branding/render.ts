/** Render the editable share artwork with the benchmark's bundled font. */
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
  await page.goto(new URL("social-card.html", import.meta.url).href);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: fileURLToPath(new URL("colorbench-share.png", import.meta.url)) });
} finally {
  await browser.close();
}
