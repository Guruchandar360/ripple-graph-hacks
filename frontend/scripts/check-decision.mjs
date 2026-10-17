import {chromium} from "@playwright/test";
import assert from "node:assert/strict";
const browser=await chromium.launch();
const page=await browser.newPage();
await page.goto("http://127.0.0.1:8000/");
await page.getByRole("button",{name:"Evaluation results",exact:true}).click();
await page.locator('[data-replay-id="fcc820e43a9d4addb5859a2ad5c53ea4"]').click();
for(const [width,height] of [[1280,720],[1366,768],[1440,900],[1536,864]]) {
  await page.setViewportSize({width,height});
  const box=await page.locator(".probe-results").boundingBox();
  assert(box && box.y>=0 && box.y+box.height<=height, `Probe results clipped at ${width}×${height}: ${JSON.stringify(box)}`);
}
await page.setViewportSize({width:1366,height:768});
await page.screenshot({path:"../artifacts/decision-laptop-100-percent.png"});
await browser.close();
console.log("Verified outcome remains fully visible at normal desktop zoom.");
