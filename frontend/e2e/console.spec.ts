import { test, expect } from "@playwright/test";

test("fixture preview is honest, inspectable and cannot execute recovery", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Follow the evidence." }),
  ).toBeVisible();
  await expect(
    page.getByText("FIXTURE PREVIEW", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("6 services", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Inject migration evidence" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Explore evidence" }).click();
  await page.getByPlaceholder("Search source records…").fill("schema");
  await expect(
    page.getByRole("heading", { name: "Payments v2.4 release record" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close evidence library" }).click();
  await page.getByRole("button", { name: "Start investigation" }).click();
  await expect(
    page.getByRole("heading", { name: "Connect your workspace." }),
  ).toBeVisible();
  await expect(page.getByText("Key missing", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByText("No recovery action has been proposed.", { exact: false }),
  ).toBeVisible();
});

test("all scenarios, memory and results empty states work", async ({
  page,
}) => {
  await page.route("**/api/evaluations", route => route.fulfill({json:{measured:false,cases:[],summary:null}}));
  await page.route("**/api/replays", route => route.fulfill({json:[]}));
  await page.goto("/");
  await expect(page.getByText("6 services", { exact: true })).toBeVisible();
  await page.locator(".sidebar-scenarios summary").click();
  await page.getByRole("button", { name: /03 Know what/ }).click();
  await expect(
    page.getByRole("heading", {
      name: "Checkout is failing. The cause is unclear.",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Inject migration evidence" }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: /Incident memory/ }).click();
  await expect(
    page.getByRole("heading", { name: "No incident memory yet" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Evaluation results" }).click();
  await expect(
    page.getByRole("heading", { name: "No benchmark scores claimed" }),
  ).toBeVisible();
  await expect(
    page.getByText("No live runs have been exported yet.", { exact: false }),
  ).toBeVisible();
});

test("desktop and mobile render without overflow or browser errors", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.setViewportSize({ width: 1440, height: 1040 });
  await page.goto("/");
  await expect(page.getByText("6 services", { exact: true })).toBeVisible();
  await page.screenshot({
    path: "../artifacts/ripple-desktop.png",
    fullPage: true,
  });
  for (const width of [390, 768]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(
      page.getByRole("heading", { name: "Follow the evidence." }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBeTruthy();
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page
    .getByRole("combobox", { name: "Scenario", exact: true })
    .selectOption("insufficient");
  await expect(
    page.getByRole("heading", {
      name: "Checkout is failing. The cause is unclear.",
    }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Scenario", exact: true })
    .selectOption("outdated-fix");
  await expect(
    page.getByRole("heading", {
      name: "Checkout is failing after a payments release.",
    }),
  ).toBeVisible();
  await page.screenshot({
    path: "../artifacts/ripple-mobile.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});

test("command navigation and participant checklist remain accessible and honest", async ({page}) => {
  await page.goto("/");
  await page.keyboard.press("Control+k");
  const dialog = page.getByRole("dialog", {name:"Command menu"});
  await expect(dialog).toBeVisible();
  await dialog.getByRole("textbox").fill("Launch checklist");
  await dialog.getByRole("button", {name:/Launch checklist/}).click();
  await expect(page.getByRole("heading", {name:"Ready for the spotlight."})).toBeVisible();
  await expect(page.getByText("Participant step", {exact:true})).toHaveCount(2);
  await expect(page.getByText("Preparation status is not an organizer's eligibility approval.")).toBeVisible();
});

test("readable graph and evidence use natural document scrolling at normal zoom", async ({page}) => {
  await page.goto("/");
  await expect(page.getByText("6 services", {exact:true})).toBeVisible();
  for (const [width,height] of [[1280,720],[1366,768],[1440,900],[1536,864],[1920,1080],[768,900],[390,844]]) {
    await page.setViewportSize({width,height});
    const graph=page.locator(".flow-wrapper");
    await graph.scrollIntoViewIfNeeded();
    expect((await graph.boundingBox())!.height).toBeGreaterThanOrEqual(420);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    expect(await page.evaluate(() => document.documentElement.scrollHeight > innerHeight)).toBeTruthy();
    for (const selector of [".timeline-empty", ".detail-column", ".policy-list"]) {
      expect(await page.locator(selector).evaluate(el => el.scrollHeight <= el.clientHeight + 1), `${selector} must not clip content`).toBeTruthy();
    }
    await page.getByRole("button", {name:"Jump to sources",exact:true}).click();
    await expect(page.locator(".inspector")).toBeFocused();
    await expect(page.getByRole("heading", {name:"Evidence library",exact:true})).toBeInViewport();
    await page.getByRole("button", {name:"Jump to recovery decision",exact:true}).click();
    await expect(page.locator(".recommendation")).toBeInViewport();
    await page.locator(".policy-list > button").first().click();
    await expect(page.getByRole("heading", {name:"Selected context",exact:true})).toBeInViewport();
    await page.getByRole("button", {name:"Clear selected context"}).click();
    await page.locator(".page-footer").scrollIntoViewIfNeeded();
    await expect(page.locator(".page-footer")).toBeInViewport();
  }
  await page.setViewportSize({width:1366,height:768});
  await page.evaluate(() => scrollTo(0,0));
  await page.screenshot({path:"../artifacts/ripple-redesign-desktop.png"});
  await page.locator(".graph-panel").screenshot({path:"../artifacts/ripple-redesign-graph.png"});
  for (const [width,height] of [[1280,600],[1024,600],[390,600]]) {
    await page.setViewportSize({width,height});
    await page.getByRole("button", {name:"Explore evidence"}).click();
    const bounds = await page.getByRole("dialog").boundingBox();
    expect(bounds!.y).toBeGreaterThanOrEqual(0);
    expect(bounds!.y + bounds!.height).toBeLessThanOrEqual(height + 1);
    await page.keyboard.press("Escape");
  }
});

test("mobile navigation drawer supports keyboard, scenarios and all views", async ({page}) => {
  await page.setViewportSize({width:390,height:844});
  await page.goto("/");
  const menu=page.getByRole("button", {name:"Open navigation",exact:true});
  await menu.click();
  await expect(menu).toHaveAttribute("aria-expanded","true");
  await expect(page.getByRole("button", {name:"Close navigation",exact:true})).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(page.getByRole("button", {name:"New investigation",exact:true})).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(menu).toBeFocused();
  await menu.click();
  await page.getByRole("button", {name:"Incident memory",exact:true}).click();
  await expect(menu).toHaveAttribute("aria-expanded","false");
  await expect(page.getByRole("heading", {name:"Remember what worked.",exact:true})).toBeVisible();
  await menu.click();
  await page.locator(".sidebar-scenarios summary").click();
  await page.getByRole("button", {name:/03 Know what/}).click();
  await expect(page.getByRole("heading", {name:"Checkout is failing. The cause is unclear.",exact:true})).toBeVisible();
});

test("memory, measured results and checklist adapt to phone, tablet and laptop widths", async ({page}) => {
  await page.goto("/");
  for (const [width,height] of [[390,844],[768,900],[1024,768],[1366,768]]) {
    await page.setViewportSize({width,height});
    for (const [button,heading] of [["Incident memory","Remember what worked."],["Evaluation results","Show the evidence."],["Launch checklist","Ready for the spotlight."]]) {
      if (width <= 900) await page.getByRole("button", {name:"Open navigation",exact:true}).click();
      await page.getByRole("button", {name:button,exact:true}).click();
      await expect(page.getByRole("heading", {name:heading,exact:true})).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${button} has no page overflow at ${width}`).toBeTruthy();
      await page.evaluate(() => scrollTo(0,document.documentElement.scrollHeight));
      expect(await page.evaluate(() => scrollY + innerHeight >= document.documentElement.scrollHeight - 2)).toBeTruthy();
    }
  }
});

test("a late startup response cannot replace a selected recorded graph", async ({page}) => {
  let releaseHealth!: () => void;
  const gate = new Promise<void>(resolve => { releaseHealth=resolve; });
  await page.route("**/api/health", async route => {
    await gate;
    await route.fulfill({json:{database:"unavailable",model:"unconfigured",model_configured:false,limits:{workspace_daily:3,global_daily:10}}});
  });
  await page.goto("/");
  await page.getByRole("button", {name:"Evaluation results",exact:true}).click();
  await page.locator('[data-replay-id="fcc820e43a9d4addb5859a2ad5c53ea4"]').click();
  const healthResponse=page.waitForResponse("**/api/health");
  releaseHealth();
  await healthResponse;
  await page.waitForLoadState("networkidle");
  await expect(page.getByText("REPLAY", {exact:true})).toBeVisible();
  await expect(page.locator(".context-metric").filter({hasText:"Evidence revision"}).locator("strong")).toHaveText("4");
  await expect(page.getByText("Recovery confirmed by probes",{exact:true})).toBeVisible();
});
