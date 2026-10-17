import {chromium} from "@playwright/test";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
const browser=await chromium.launch();
const page=await browser.newPage();
await page.goto("http://127.0.0.1:8000/");
await page.getByRole("button",{name:"Evaluation results",exact:true}).click();
await page.locator('[data-replay-id="fcc820e43a9d4addb5859a2ad5c53ea4"]').click();
for(const [width,height] of [[1280,720],[1366,768],[1440,900],[1536,864]]) {
  await page.setViewportSize({width,height});
  await page.locator(".probe-results").scrollIntoViewIfNeeded();
  const box=await page.locator(".probe-results").boundingBox();
  assert(box && box.y>=0 && box.y+box.height<=height, `Probe results clipped at ${width}×${height}: ${JSON.stringify(box)}`);
  assert(await page.locator(".proposal-rationale").evaluate(el => el.scrollHeight <= el.clientHeight + 1));
}
await page.setViewportSize({width:1366,height:768});
await page.locator(".recommendation").screenshot({path:fileURLToPath(new URL("../../artifacts/decision-laptop-100-percent.png",import.meta.url))});
await browser.close();
console.log("Verified probes are reachable at normal zoom; the complete rationale uses natural page flow.");
