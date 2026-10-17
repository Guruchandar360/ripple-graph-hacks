import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e", testMatch: "showcase.spec.ts", workers: 1,
  use: { baseURL: "http://127.0.0.1:4173/ripple-graph-hacks/", headless: true },
  webServer: { command: "npx vite preview --host 127.0.0.1 --port 4173", url: "http://127.0.0.1:4173/ripple-graph-hacks/", reuseExistingServer: false },
});
