import { test as setup } from '@playwright/test'
import { DEMO_EMAIL, DEMO_PASSWORD } from './helpers'

const authFile = '.auth/demo.json'

// Logs in once via the real UI and saves the resulting session (localStorage
// token) to disk. dashboard.spec.ts and chat.spec.ts reuse this instead of
// each performing their own UI login — auth.spec.ts is the one place that's
// actually testing the login flow itself, so it deliberately does NOT use
// this saved state (see the "auth-flows" project in playwright.config.ts).
// This also matters for a reason beyond speed: /auth/login is rate-limited
// to 8/minute, and every test independently logging in was enough on its
// own to trip that limit across a couple of back-to-back suite runs.
setup('authenticate as the demo user', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Email').fill(DEMO_EMAIL)
  await page.getByLabel('Password').fill(DEMO_PASSWORD)
  await page.getByRole('button', { name: 'Login', exact: true }).click()
  await page.waitForURL('/')

  await page.context().storageState({ path: authFile })
})
