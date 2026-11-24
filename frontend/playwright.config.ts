import { defineConfig, devices } from "@playwright/test";

const python = process.env.CI ? "python" : ".venv/bin/python";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  workers: 1,
  use: { ...devices["Desktop Chrome"], baseURL: "http://127.0.0.1:5173" },
  webServer: [
    {
      command: `${python} -m uvicorn app.main:app --host 127.0.0.1 --port 8000`,
      cwd: "../backend",
      port: 8000,
      reuseExistingServer: !process.env.CI,
      env: {
        APP_DISABLE_DOTENV: "1",
        DATABASE_URL: "sqlite:///./data/e2e.db",
        AI_PROVIDER: "mock",
        OPENAI_API_KEY: "",
        ANTHROPIC_API_KEY: "",
      },
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5173",
      port: 5173,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
