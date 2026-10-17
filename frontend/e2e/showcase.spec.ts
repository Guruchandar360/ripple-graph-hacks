import { test, expect } from "@playwright/test";
test.skip(!process.env.STATIC_QA, "Requires the separately built read-only showcase");
test("showcase loads under its public subpath and cannot send live mutations", async ({ page }) => {
  const mutations: string[] = [];
  const errors: string[] = [];
  page.on("request", r => { if (r.method() !== "GET") mutations.push(r.url()); });
  page.on("pageerror", e => errors.push(e.message));
  const recordingResponse=page.waitForResponse(r => r.url().endsWith("/showcase/replays.json"));
  await page.goto("./");
  const records=await (await recordingResponse).json();
  if (records.some((r:{mode:string;status:string}) => r.mode==="graph" && r.status==="recovered")) {
    await expect(page.getByText("REPLAY", {exact:true})).toBeVisible();
  }
  await expect(page.getByText("Recorded showcase", {exact:true})).toBeVisible();
  await expect(page.getByText("6 services", {exact:true})).toBeVisible();
  if (await page.locator(".probe-results").count()) {
    await expect(page.locator(".probe-results")).toBeInViewport();
    const probe = await page.locator(".probe-results").boundingBox();
    expect(probe!.y + probe!.height).toBeLessThanOrEqual(page.viewportSize()!.height);
  }
  const start = page.getByRole("button", {name:"Start investigation",exact:true});
  if (await start.count()) {
    await start.click();
    await expect(page.getByRole("heading", {name:"Connect your workspace."})).toBeVisible();
    await page.keyboard.press("Escape");
  } else {
    await expect(page.getByRole("button", {name:"Investigate again",exact:true})).toBeDisabled();
  }
  await page.getByRole("button", {name:"Evaluation results"}).click();
  await expect(page.getByRole("heading", {name:"Show the evidence."})).toBeVisible();
  const replay = page.locator('[data-replay-id]').first();
  if (await replay.count()) {
    await replay.click();
    await expect(page.getByText("REPLAY", {exact:true})).toBeVisible();
    await expect(page.getByText("RECORDED GRAPH", {exact:true})).toBeVisible();
    await expect(page.getByRole("button", {name:"Investigate again"})).toBeDisabled();
    const supporting = page.getByRole("button", {name:"Show supporting paths",exact:true}).first();
    if (await supporting.count()) {
      await supporting.click();
      await expect(page.locator(".event-selected")).toHaveCount(1);
      await expect(page.locator(".react-flow__edge-text").first()).toHaveText("depends on");
    }
  }
  for (const [width,height] of [[390,844],[768,900],[1280,720],[1366,768],[1440,900]]) {
    await page.setViewportSize({width,height});
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    if (width >= 1200) {
      for (const selector of [".graph-panel", ".timeline-panel", ".page-footer"]) {
        await expect(page.locator(selector)).toBeInViewport();
      }
      await page.getByRole("button", {name:"Jump to sources",exact:true}).click();
      await expect(page.locator(".inspector")).toBeInViewport();
      await expect(page.locator(".inspector")).toBeFocused();
      await page.getByRole("button", {name:"Jump to recovery decision",exact:true}).click();
      await expect(page.locator(".recommendation")).toBeInViewport();
    }
  }
  expect(mutations).toEqual([]);
  expect(errors).toEqual([]);
});
