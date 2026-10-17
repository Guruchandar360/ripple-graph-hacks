import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";

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
  await page.waitForFunction(() => document.documentElement.scrollWidth <= innerWidth);
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  assert((await page.locator(".flow-wrapper").boundingBox()).height >= 420);
  for (const selector of [".timeline", ".detail-column", ".proposal-rationale"]) {
    assert(await page.locator(selector).evaluate(el => el.scrollHeight <= el.clientHeight + 1), `${selector} must expand with its content`);
  }
}
await page.setViewportSize({width:1366,height:768});
await page.getByRole("button", {name:"Jump to sources",exact:true}).click();
assert(await page.locator(".inspector").evaluate(el => document.activeElement === el));
await page.getByRole("button", {name:"Jump to recovery decision",exact:true}).click();
await page.evaluate(() => scrollTo(0,0));
await page.screenshot({path:fileURLToPath(new URL("../../artifacts/public-laptop-100-percent.png", import.meta.url))});
const video = await page.request.get("https://guruchandar360.github.io/ripple-graph-hacks/showcase/ripple-demo.mp4");
assert.equal(video.status(), 200);
assert(video.headers()["content-type"].includes("video/mp4"));
assert.deepEqual(errors, []);
await browser.close();
console.log("Published showcase: natural scrolling, readable graph and evidence navigation passed; MP4 served successfully; no browser errors.");
