import { defineConfig, devices } from '@playwright/test'

// Real end-to-end tests: a real Chromium browser driving the actual built
// frontend against the actual running FastAPI backend and the real OpenAI
// API — not the mocked network of the unit/integration suites in
// frontend/src/**/*.test.tsx or api/tests/. That's the point of this
// layer: catch what mocking can't (real CORS, real cookies/localStorage,
// real navigation, real timing) — see e2e/README.md for the cost/scope
// tradeoffs that come with hitting the real backend.
export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'setup',
      testMatch: /auth\.setup\.ts/,
    },
    {
      // Actually exercises the login/register UI, so it must start
      // unauthenticated — no storageState, no dependency on 'setup'.
      name: 'auth-flows',
      testMatch: /auth\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      // Everything else just needs to *be* logged in to test something
      // unrelated — reuses the session 'setup' already established instead
      // of each test performing its own UI login.
      name: 'authenticated',
      testMatch: /(dashboard|chat)\.spec\.ts/,
      use: { ...devices['Desktop Chrome'], storageState: '.auth/demo.json' },
      dependencies: ['setup'],
    },
  ],
  webServer: [
    {
      command: 'python -m uvicorn api.main:app --port 8000',
      cwd: '..',
      url: 'http://localhost:8000/health',
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      command: 'npm run dev',
      cwd: '../frontend',
      url: 'http://localhost:5173',
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
})
