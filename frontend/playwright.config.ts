import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  timeout: 45000,
  expect: { timeout: 15000 },
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:8000",
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command:
      process.platform === "win32"
        ? "..\\.venv\\Scripts\\python -m uvicorn ripple.main:app --app-dir .. --host 127.0.0.1 --port 8000"
        : "../.venv/bin/python -m uvicorn ripple.main:app --app-dir .. --host 127.0.0.1 --port 8000",
    url: "http://127.0.0.1:8000/api/scenarios",
    reuseExistingServer: true,
    timeout: 30000,
  },
});
