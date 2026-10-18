// Records the actual exported application state, never synthesizes model output.
import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const destination = path.resolve("../demo");
const smoke = process.argv.includes("--smoke");
const repetition = process.env.DEMO_REPETITION;
await mkdir(destination, { recursive: true });
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, recordVideo: { dir: path.resolve("../artifacts/video"), size: { width: 1440, height: 1000 } } });
const page = await context.newPage();
const errors = [];
page.on("pageerror", e => errors.push(e.message));
await page.goto(process.env.DEMO_URL || "http://127.0.0.1:8000/");
await page.getByText("6 services", { exact: true }).waitFor();

async function caption(title, detail, seconds = 7) {
  await page.evaluate(({ title, detail }) => {
    document.getElementById("recording-caption")?.remove();
    const card = document.createElement("aside");
    card.id = "recording-caption";
    card.style.cssText = "position:fixed;bottom:24px;left:280px;right:360px;z-index:9999;background:rgba(9,20,28,.97);border:1px solid #3e8a72;border-radius:14px;padding:17px 22px;box-shadow:0 8px 50px #000b;pointer-events:none;font-family:system-ui;color:#e6f0f6;";
    const label = document.createElement("div"); label.textContent = "RECORDED DEMONSTRATION · SYNTHETIC DATA";
    label.style.cssText = "font:12px monospace;letter-spacing:.08em;color:#65d8b0;margin-bottom:8px";
    const heading = document.createElement("strong"); heading.textContent = title; heading.style.cssText = "display:block;font-size:19px;margin-bottom:5px";
    const text = document.createElement("div"); text.textContent = detail; text.style.cssText = "font-size:15px;color:#b7c8d1;line-height:1.6";
    card.append(label, heading, text); document.body.append(card);
  }, { title, detail });
  await page.waitForTimeout(seconds * 1000);
}
async function results() {
  await page.getByRole("button", { name: "Evaluation results", exact: true }).click();
  await page.getByRole("heading", { name: "Show the evidence." }).waitFor();
  await page.locator(".comparison-panel").waitFor();
  await page.locator(".comparison-panel").evaluate(el => el.scrollIntoView({block:"center",behavior:"instant"}));
}
async function openCase(id, expected, phase) {
  await results();
  const sequence = repetition ? `[data-replay-repetition="${repetition}"][data-replay-phase="${phase}"]` : "";
  const selectedId = process.env[`DEMO_${phase.toUpperCase()}_ID`];
  const selection = selectedId ? `[data-replay-id="${selectedId}"]` : sequence;
  const row = page.locator(`[data-replay-case="${id}"][data-replay-mode="graph"]${selection}`).first();
  if (!(await row.count())) throw new Error(`Required actual graph replay ${id} is absent; refusing to fake a demo.`);
  if (expected && await row.getAttribute("data-replay-status") !== expected) throw new Error(`Actual ${id} did not reach ${expected}; refusing to present it as successful.`);
  if (phase === "memory" && Number(await row.getAttribute("data-replay-memory-count")) < 1) throw new Error("This run did not retrieve memory; refusing to claim it did.");
  await row.click();
  await page.getByText("REPLAY", { exact: true }).waitFor();
  await page.evaluate(() => scrollTo(0, 0));
}
await caption("Yesterday’s fix can break today’s system.", "Ripple follows connected evidence, rechecks recommendations and verifies simulator recovery. All model output shown next was recorded from actual runs.", 8);
await results();
await caption("Measured behavior, including limitations.", smoke ? "This is the development smoke test. Both modes recovered; their reported impact sets were incomplete. It is not the full 12-case benchmark." : "Both workflows use the same model, source documents, probe capabilities and eight-turn budget. This small synthetic evaluation does not establish general superiority.", 9);
await openCase(smoke ? "C01" : "C02", "recovered", "recovery");
await page.locator(".graph-panel").evaluate(el => el.scrollIntoView({block:"center",behavior:"instant"}));
await caption("The graph changes what an action is allowed to do.", "A newer ledger advisory supersedes the old compatibility record. These service paths and action policies were retrieved from FalkorDB.", 8);
const changed = page.locator(".timeline-event").filter({ hasText: "Evidence changed" }).first();
if (!smoke) {
if (!(await changed.count())) throw new Error("The actual evidence-change event is missing.");
await changed.scrollIntoViewIfNeeded();
await caption("Evidence changed. Old approvals cannot execute.", "The timeline retains the earlier investigation and the migration event. Ripple starts a fresh model conversation against the current graph revision.", 9);
} else {
  await page.locator(".policy-list > button").first().click();
  await caption("Inspect the policy and its original evidence.", "The ledger migration blocks rollback while permitting a scoped flag change. The selected source is available without leaving the investigation.", 9);
}
await page.locator(".recommendation").scrollIntoViewIfNeeded();
await caption("An action is not a recovery until the probes pass.", "Inspect the actual before → after request status codes. The simulator transition and its audit result are persisted together; actions are disabled in this replay.", 9);
if (!smoke) {
await openCase("C08", "recovered", "memory");
const memory = page.locator(".timeline-event").filter({ hasText: "Incident memory retrieved" }).first();
await memory.scrollIntoViewIfNeeded();
await caption("A fresh conversation remembers through the graph.", "FalkorDB supplies persisted, measured outcomes to a fresh model conversation. Current constraints still apply; earlier chat messages are not carried over." + (process.env.DEMO_MEMORY_BOOTSTRAP ? " This benchmark uses a verified simulator-bootstrap outcome." : ""), 11);
await openCase("C10", "needs_evidence", "insufficient");
await page.locator(".timeline").scrollIntoViewIfNeeded();
await caption("Insufficient evidence means no executed remediation.", "The agent can identify missing diagnostics and stop. Deterministic guards provide an independent boundary if the model proposes an unsafe action.", 9);
}
await results();
await caption("Public source. Reproducible. Explicit limits.", "github.com/Guruchandar360/ripple-graph-hacks · Actual Qwen/Ollama runs with FalkorDB. Synthetic infrastructure, AI-assisted implementation, and complete local setup are disclosed.", 10);
const video = page.video();
await context.close();
const filename = smoke ? "ripple-smoke-demo.webm" : "ripple-demo.webm";
await video.saveAs(path.join(destination, filename));
await browser.close();
if (errors.length) throw new Error(errors.join("\n"));
console.log(`Recorded actual application output: ${path.join(destination, filename)}`);
