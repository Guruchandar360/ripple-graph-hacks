import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const output = fileURLToPath(new URL("../../artifacts/", import.meta.url));
await mkdir(output, { recursive: true });
const luminance = hex => {
  const channels = hex.match(/[a-f\d]{2}/gi).map(v => parseInt(v, 16) / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
  return channels[0] * .2126 + channels[1] * .7152 + channels[2] * .0722;
};
const paletteChecks = [
  ["Body", "#eaf1ed", "#111a16"],
  ["Secondary", "#a2b2a9", "#111a16"],
  ["Labels", "#96a89d", "#111a16"],
  ["Primary button", "#07291e", "#2dd4a7"],
  ["Graph metadata", "#a9c5b3", "#1d3026"],
].map(([name, foreground, background]) => {
  const values = [luminance(foreground), luminance(background)].sort((a,b) => b-a);
  const contrast = (values[0] + .05) / (values[1] + .05);
  assert(contrast >= 4.5, `${name} must meet WCAG AA normal-text contrast`);
  return {name, contrast: Number(contrast.toFixed(2))};
});
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, reducedMotion: "reduce" });
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(process.env.RIPPLE_QA_URL ?? "http://127.0.0.1:8000/");
  await page.getByRole("button", { name: "Evaluation results", exact: true }).click();
  await page.locator('[data-replay-id="fcc820e43a9d4addb5859a2ad5c53ea4"]').click();
  await page.getByText("REPLAY", { exact: true }).waitFor();
  await page.evaluate(() => document.fonts.ready);
  assert(await page.evaluate(() => document.fonts.check("15px Inter") && document.fonts.check('12px "JetBrains Mono"')), "Bundled fonts must load");
  const report = [];
  for (const [width, height] of [[1440, 1000], [1366, 768], [768, 900], [390, 844], [360, 800]]) {
    await page.setViewportSize({ width, height });
    await page.waitForFunction(() => document.documentElement.scrollWidth <= innerWidth);
    await page.getByRole("button", { name: "Fit graph to panel", exact: true }).click();
    await page.locator(".flow-wrapper").scrollIntoViewIfNeeded();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth ? [] : Array.from(document.querySelectorAll("main *,header *")).filter(el => {
      const r=el.getBoundingClientRect(); return r.width && r.right > innerWidth + 1 && !el.closest(".react-flow");
    }).map(el => ({tag:el.tagName,classes:el.className,width:el.getBoundingClientRect().width})).slice(0,15));
    assert.deepEqual(overflow, [], `Page overflow at ${width}`);
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Document overflow at ${width}`);
    const metrics = await page.evaluate(() => {
      const tiny = [];
      const walker = document.createTreeWalker(document.querySelector("main"), NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        const text = walker.currentNode;
        const el = text.parentElement;
        if (!text.textContent.trim() || !el?.getClientRects().length || el.closest("svg")) continue;
        const style = getComputedStyle(el);
        if (style.visibility === "hidden") continue;
        if (parseFloat(style.fontSize) < 12) tiny.push({ text: text.textContent.trim().slice(0, 60), size: style.fontSize });
      }
      const node = document.querySelector(".service-node");
      const scale = node.getBoundingClientRect().width / node.offsetWidth;
      return { tiny, graphLabelPixels: parseFloat(getComputedStyle(node.querySelector("strong")).fontSize) * scale,
        graphHeight: document.querySelector(".flow-wrapper").clientHeight,
        clipped: [".timeline", ".detail-column", ".proposal-rationale", ".policy-list"].filter(selector => {
          const el = document.querySelector(selector);
          return el && el.scrollHeight > el.clientHeight + 1;
        }) };
    });
    assert.deepEqual(metrics.tiny, [], `Text below 12px at ${width}`);
    assert.deepEqual(metrics.clipped, [], `Clipped content at ${width}`);
    assert(metrics.graphLabelPixels >= 12, `Graph labels too small at ${width}`);
    await page.evaluate(() => scrollTo(0, 0));
    await page.screenshot({ path: `${output}/redesign-${width}.png` });
    await page.locator(".graph-panel").screenshot({ path: `${output}/redesign-graph-${width}.png` });
    report.push({ width, height, ...metrics });
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.locator(".investigation-columns").evaluate(el => el.scrollIntoView({block:"start"}));
  await page.screenshot({ path: `${output}/redesign-investigation.png` });
  await page.locator(".recommendation").screenshot({ path: `${output}/redesign-recovery.png` });
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({paletteChecks, viewports:report}, null, 2));
} finally {
  await browser.close();
}
