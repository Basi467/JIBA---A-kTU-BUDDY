# JIBA end-to-end tests (Playwright)

Real Chromium driving the actual built frontend against the actual running
FastAPI backend — and for the chat test, the real OpenAI API. Separate from
and complementary to:

- `api/tests/` — pytest, real FastAPI `TestClient`, real (temp) database, mocked OpenAI client
- `frontend/src/**/*.test.tsx` — Vitest/RTL, real DOM (jsdom), mocked network via MSW
- `api/evals/` — real OpenAI API calls, but graded on *response quality*, not app behavior

This layer exists to catch what mocking can't: real CORS behavior, real
cookies/localStorage, real navigation, real focus/keyboard behavior, real
timing. `dashboard.spec.ts`'s insights-drawer test in particular is a
permanent regression test for a real bug found earlier in this project — a
Framer Motion exit animation that never unmounted the dialog, leaving it
focusable in the DOM after "closing" it.

## Running it

```bash
cd e2e
npm install          # first time only
npx playwright install chromium   # first time only
npm test
```

By default this reuses whatever's already running on :8000 and :5173
(`reuseExistingServer: !process.env.CI` in `playwright.config.ts`) — if
neither is running, Playwright starts both for you and tears them down
after.

## Cost and state, read before running repeatedly

- **`chat.spec.ts` hits the real OpenAI API** — one real, billed API call
  per run. Kept to a single test case for exactly this reason.
- **`auth.spec.ts`'s register test creates a real account** in whatever
  database the backend is pointed at, with a timestamp-suffixed email so
  repeat runs don't collide — but nothing cleans these up automatically.
  Fine against a disposable/dev database; be deliberate about running it
  against a database you care about keeping tidy.
- Everything else (login, exam mode, the insights drawer) is read-only or
  operates on the fixed demo account and doesn't accumulate state.
- **Don't run the full suite twice within the same ~60 seconds.**
  `/auth/login` is rate-limited to 8/minute (a real backend safeguard, not
  a test artifact — see `api/limiter.py`). One full run costs 5 real login
  calls (4 in `auth-flows` + 1 in the `setup` project other tests reuse);
  two back-to-back runs can tip over the limit and fail with a
  `waitForURL` timeout in whichever test logs in next. That's the rate
  limiter correctly doing its job, not a bug — just wait a minute between
  repeat runs.

## Not yet wired into CI

The GitHub Actions workflow (`.github/workflows/ci.yml`) doesn't run this
suite — it would need a real `OPENAI_API_KEY` as a repo secret to run the
chat test (or that test would need to be skipped in CI), which is a
repo-owner action, not something addable from here.
