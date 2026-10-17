import { chromium } from "@playwright/test";
import assert from "node:assert/strict";

const browser = await chromium.launch();
const page = await browser.newPage({viewport:{width:1366,height:768}});
const errors = [];
page.on("pageerror", error => errors.push(error.message));
const response = await page.goto("https://guruchandar360.github.io/ripple-graph-hacks/");
assert.equal(response.status(), 200);
await page.getByText("Recorded showcase", {exact:true}).waitFor();
await page.getByText("REPLAY", {exact:true}).waitFor();
for (const [width,height] of [[1280,720],[1366,768],[1536,864],[1920,1080],[390,844]]) {
  await page.setViewportSize({width,height});
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  if (width >= 1200) {
    for (const selector of [".graph-panel", ".timeline-panel", ".page-footer"]) {
      const bounds = await page.locator(selector).boundingBox();
      assert(bounds && bounds.y >= 0 && bounds.y + bounds.height <= height + 1, `${selector} at ${width}×${height}`);
    }
  }
}
await page.setViewportSize({width:1366,height:768});
await page.screenshot({path:"../artifacts/public-laptop-100-percent.png"});
const video = await page.request.get("https://guruchandar360.github.io/ripple-graph-hacks/showcase/ripple-demo.mp4");
assert.equal(video.status(), 200);
assert(video.headers()["content-type"].includes("video/mp4"));
assert.deepEqual(errors, []);
await browser.close();
console.log("Published showcase: viewport checks passed; MP4 served successfully; no browser errors.");
