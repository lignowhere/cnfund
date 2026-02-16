import path from "path";
import { defineConfig, devices } from "@playwright/test";

const frontendDir = __dirname;
const backendDir = path.resolve(__dirname, "../backend_api");

export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { outputFolder: "../output/playwright/report" }]],
  outputDir: "../output/playwright/results",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "android-chrome",
      use: {
        ...devices["Pixel 7"],
      },
    },
    {
      name: "ios-safari",
      use: {
        ...devices["iPhone 14"],
        browserName: "webkit",
      },
    },
  ],
  webServer: [
    {
      command: "python -m uvicorn app.main:app --host 127.0.0.1 --port 8001",
      cwd: backendDir,
      url: "http://127.0.0.1:8001/health",
      reuseExistingServer: true,
      timeout: 120_000,
      env: {
        ...process.env,
        API_DATABASE_URL: "sqlite:///./playwright.db",
      },
    },
    {
      command: "npm run dev",
      cwd: frontendDir,
      url: "http://127.0.0.1:3000",
      reuseExistingServer: true,
      timeout: 120_000,
      env: {
        ...process.env,
        NEXT_PUBLIC_API_BASE_URL: "http://127.0.0.1:8001/api/v1",
      },
    },
  ],
});
