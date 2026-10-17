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
  await page.goto("/");
  await expect(page.getByText("6 services", { exact: true })).toBeVisible();
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
