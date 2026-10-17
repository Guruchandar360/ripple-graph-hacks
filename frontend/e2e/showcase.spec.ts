import { test, expect } from "@playwright/test";
test.skip(!process.env.STATIC_QA, "Requires the separately built read-only showcase");
test("showcase loads under its public subpath and cannot send live mutations", async ({ page }) => {
  const mutations: string[] = [];
  const errors: string[] = [];
  page.on("request", r => { if (r.method() !== "GET") mutations.push(r.url()); });
  page.on("pageerror", e => errors.push(e.message));
  await page.goto("./");
  await expect(page.getByText("Recorded showcase", {exact:true})).toBeVisible();
  await expect(page.getByText("6 services", {exact:true})).toBeVisible();
  await page.getByRole("button", {name:"Start investigation"}).click();
  await expect(page.getByRole("heading", {name:"Connect your workspace."})).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByRole("button", {name:"Evaluation results"}).click();
  await expect(page.getByRole("heading", {name:"Show the evidence."})).toBeVisible();
  const replay = page.locator('[data-replay-id]').first();
  if (await replay.count()) {
    await replay.click();
    await expect(page.getByText("REPLAY", {exact:true})).toBeVisible();
    await expect(page.getByText("RECORDED GRAPH", {exact:true})).toBeVisible();
    await expect(page.getByRole("button", {name:"Investigate again"})).toBeDisabled();
  }
  for (const width of [390, 768, 1440]) {
    await page.setViewportSize({width,height:1000});
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  }
  expect(mutations).toEqual([]);
  expect(errors).toEqual([]);
});
