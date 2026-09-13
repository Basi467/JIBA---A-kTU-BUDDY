import { expect, test } from '@playwright/test'
import { DEMO_EMAIL, DEMO_PASSWORD, loginAsDemo } from './helpers'

test('logging in with the wrong password shows an error', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Email').fill(DEMO_EMAIL)
  await page.getByLabel('Password').fill('definitely-the-wrong-password')
  await page.getByRole('button', { name: 'Login', exact: true }).click()

  await expect(page.getByText('Invalid email or password')).toBeVisible()
  await expect(page).toHaveURL('/login')
})

test('logging in with the demo account reaches the dashboard', async ({ page }) => {
  await loginAsDemo(page)
  await expect(page.getByRole('button', { name: /select subject/i })).toBeVisible()
})

test('logging out returns to the login page', async ({ page }) => {
  await loginAsDemo(page)

  await page.getByRole('button', { name: /account menu for/i }).click()
  await page.getByText('Logout').click()

  await expect(page).toHaveURL('/login')
  await expect(page.getByText('Welcome back')).toBeVisible()
})

test('registering a new account and logging in with it', async ({ page }) => {
  const email = `e2e.test.${Date.now()}@example.com`

  await page.goto('/login')
  await page.getByRole('button', { name: 'register', exact: true }).click()

  await page.locator('#register-name').fill('E2E Test User')
  await page.locator('#register-email').fill(email)
  await page.locator('#register-password').fill('e2eTestPass1')
  await page.locator('#register-confirm-password').fill('e2eTestPass1')

  // The scheme/department/semester selects populate asynchronously from
  // /meta/signup-options and default to the first option — just wait for
  // them to be enabled rather than picking specific values.
  await expect(page.locator('#register-scheme')).toBeEnabled()

  await page.getByRole('button', { name: /create account/i }).click()
  await expect(page.getByText('Account created. Redirecting to login...')).toBeVisible()

  // RegisterForm stays mounted for ~900ms after showing that message before
  // auto-switching tabs — filling by label too early fills its own
  // (already-submitted) fields instead of the login form's. Wait for the
  // actual switch (LoginForm's heading) before interacting with it.
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill('e2eTestPass1')
  await page.getByRole('button', { name: 'Login', exact: true }).click()

  await page.waitForURL('/')
  await expect(page.getByRole('button', { name: /select subject/i })).toBeVisible()
})
