import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  timeout: 45000,
  expect: { timeout: 15000 },
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:8100",
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command:
      process.platform === "win32"
        ? "..\\.venv\\Scripts\\python -m uvicorn ripple.main:app --app-dir .. --host 127.0.0.1 --port 8100"
        : "../.venv/bin/python -m uvicorn ripple.main:app --app-dir .. --host 127.0.0.1 --port 8100",
    url: "http://127.0.0.1:8100/api/scenarios",
    reuseExistingServer: false,
    // These checks exercise the honest disconnected preview, never .env services.
    env: {
      MODEL_PROVIDER: "gemini",
      GEMINI_API_KEY: "",
      FALKORDB_HOST: "127.0.0.1",
      FALKORDB_PORT: "1",
      FALKORDB_USERNAME: "",
      FALKORDB_PASSWORD: "",
      FALKORDB_SSL: "false",
      FALKORDB_CONTROL_GRAPH: "ripple_browser_test_control",
      COOKIE_SECURE: "false",
    },
    timeout: 30000,
  },
});
