import type { Page } from '@playwright/test'

export const DEMO_EMAIL = 'aisha.demo@example.com'
export const DEMO_PASSWORD = 'Demo@1234'

export async function loginAsDemo(page: Page) {
  await page.goto('/login')
  await page.getByLabel('Email').fill(DEMO_EMAIL)
  await page.getByLabel('Password').fill(DEMO_PASSWORD)
  await page.getByRole('button', { name: 'Login', exact: true }).click()
  await page.waitForURL('/')
}
