import { expect, test } from '@playwright/test'

// Runs in the 'authenticated' project (playwright.config.ts), which loads
// the demo session saved by auth.setup.ts — no UI login needed per test.
test.beforeEach(async ({ page }) => {
  await page.goto('/')
})

test('toggling exam mode shows the Exam Mode heading and tabs', async ({ page }) => {
  await page.getByRole('switch', { name: /toggle exam mode/i }).click()

  await expect(page.getByRole('heading', { name: 'Exam Mode' })).toBeVisible()
  await expect(page.getByRole('button', { name: /overview/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /teach high priority/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /solve repeated pyqs/i })).toBeVisible()
})

test('switching exam mode tabs changes the visible content', async ({ page }) => {
  await page.getByRole('switch', { name: /toggle exam mode/i }).click()
  await expect(page.getByRole('heading', { name: 'Exam Mode' })).toBeVisible()

  await page.getByRole('button', { name: /teach high priority/i }).click()
  await expect(
    page.getByRole('button', { name: /start teaching high priority topics/i }),
  ).toBeVisible()

  await page.getByRole('button', { name: /solve repeated pyqs/i }).click()
  await expect(page.getByRole('button', { name: /start solving repeated pyqs/i })).toBeVisible()
})

test('the mobile insights drawer opens with focus on close, and Escape closes it with focus restored', async ({
  page,
}) => {
  // The insights button only renders at narrow viewports (xl:hidden).
  await page.setViewportSize({ width: 500, height: 900 })
  await page.goto('/')

  const trigger = page.getByRole('button', { name: /progress & insights/i })
  await trigger.click()

  const dialog = page.getByRole('dialog', { name: 'Insights' })
  await expect(dialog).toBeVisible()
  await expect(page.getByRole('button', { name: /close insights/i })).toBeFocused()

  await page.keyboard.press('Escape')

  await expect(dialog).not.toBeVisible()
  await expect(trigger).toBeFocused()
})
