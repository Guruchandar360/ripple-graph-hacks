import { test, expect } from "@playwright/test";
test.skip(!process.env.STATIC_QA, "Requires the separately built read-only showcase");
test("proof guide keeps measurements and raw evidence accessible at desktop and mobile sizes", async ({ page }) => {
  await page.goto("./proof/");
  await expect(page.getByRole("heading", {name:"Every claim has an evidence trail."})).toBeVisible();
  for (const width of [390, 768, 1366]) {
    await page.setViewportSize({width, height:900});
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  }
  const report = await (await page.request.get("./showcase/evaluations.json")).json();
  for (const [index, mode] of ["graph", "baseline"].entries()) {
    const cases = report.cases.filter((row:{mode:string}) => row.mode === mode);
    await expect(page.locator("tbody tr").nth(index).locator("td").first()).toHaveText(`${cases.filter((row:{expected_met:boolean}) => row.expected_met).length}/12`);
  }
  const urls = await page.locator('a[href^="../showcase/"]').evaluateAll(links => [...new Set(links.map(el => (el as HTMLAnchorElement).href))]);
  for (const url of urls) {
    // The video has its own byte-exact audit; avoid downloading it again here.
    if (!url.endsWith(".mp4")) expect((await page.request.get(url)).status()).toBe(200);
  }
});
test("showcase loads under its public subpath and cannot send live mutations", async ({ page }) => {
  const mutations: string[] = [];
  const archiveReads: string[] = [];
  const errors: string[] = [];
  page.on("request", r => {
    if (r.method() !== "GET") mutations.push(r.url());
    if (r.url().endsWith("/showcase/replays.json")) archiveReads.push(r.url());
  });
  page.on("pageerror", e => errors.push(e.message));
  const recordingResponse=page.waitForResponse(r => r.url().endsWith("/showcase/replays.json"));
  const featuredResponse=page.waitForResponse(r => r.url().endsWith("/showcase/featured.json"));
  await page.goto("./");
  const featured=await (await featuredResponse).json();
  if (featured?.mode === "graph" && featured.status === "recovered") {
    await expect(page.getByText("REPLAY", {exact:true})).toBeVisible();
  }
  await expect(page.getByText("Recorded showcase", {exact:true})).toBeVisible();
  await expect(page.getByText("6 services", {exact:true})).toBeVisible();
  await page.getByRole("button", {name:"Dismiss workspace notice",exact:true}).click();
  await expect(page.locator(".mode-banner")).toHaveCount(0);
  await expect(page.getByText("REPLAY", {exact:true})).toBeVisible();
  if (await page.locator(".probe-results").count()) {
    await page.locator(".probe-results").scrollIntoViewIfNeeded();
    await expect(page.locator(".probe-results")).toBeInViewport();
    expect(await page.locator(".proposal-rationale").evaluate(el => el.scrollHeight <= el.clientHeight + 1)).toBeTruthy();
  }
  const start = page.getByRole("button", {name:"Start investigation",exact:true});
  if (await start.count()) {
    await start.click();
    await expect(page.getByRole("heading", {name:"Connect your workspace."})).toBeVisible();
    await page.keyboard.press("Escape");
  } else {
    await expect(page.getByRole("button", {name:"Investigate again",exact:true})).toBeDisabled();
  }
  expect(archiveReads).toHaveLength(0);
  await page.getByRole("button", {name:"Evaluation results"}).click();
  const records=await (await recordingResponse).json();
  await expect(page.getByRole("heading", {name:"Show the evidence."})).toBeVisible();
  const replay = page.locator('[data-replay-id]').first();
  if (await replay.count()) {
    const replayId = await replay.getAttribute("data-replay-id");
    await replay.click();
    await expect(page.getByText("REPLAY", {exact:true})).toBeVisible();
    await expect(page.getByText("RECORDED GRAPH", {exact:true})).toBeVisible();
    await expect(page.getByRole("button", {name:"Investigate again"})).toBeDisabled();
    const selectedRecord = records.find((r:{id:string}) => r.id === replayId);
    const pathEvents = selectedRecord?.events.filter((e:{paths?:{edges:string[]}[]}) => e.paths?.length) ?? [];
    if (pathEvents.length) {
      await page.locator(`[data-event-id="${pathEvents[0].id}"]`).getByRole("button", {name:"Show supporting paths",exact:true}).click();
      await expect(page.locator(".event-selected")).toHaveCount(1);
      if (pathEvents[0].paths.every((p:{edges:string[]}) => p.edges.length === 0)) {
        await expect(page.locator(".react-flow__edge-text")).toHaveCount(0);
      }
      const connectedPath = pathEvents.find((e:{paths:{edges:string[]}[]}) => e.paths.some(p => p.edges.length > 0));
      expect(connectedPath).toBeTruthy();
      await page.locator(`[data-event-id="${connectedPath.id}"]`).getByRole("button", {name:"Show supporting paths",exact:true}).click();
      await expect(page.locator(".react-flow__edge-text").first()).toHaveText("depends on");
    }
  }
  for (const [width,height] of [[390,844],[768,900],[1280,720],[1366,768],[1440,900]]) {
    await page.setViewportSize({width,height});
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    if (width >= 1200) {
      for (const selector of [".graph-panel", ".timeline-panel", ".page-footer"]) {
        await page.locator(selector).scrollIntoViewIfNeeded();
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
  expect(archiveReads).toHaveLength(1);
  expect(errors).toEqual([]);
});
