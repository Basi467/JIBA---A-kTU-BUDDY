import { expect, test } from '@playwright/test'

// Hits the real OpenAI API through the real backend — kept to a single
// case (see e2e/README.md) since each run costs a real API call, unlike
// the mocked chat tests in frontend/src/components/TutorChat.test.tsx.
// Runs in the 'authenticated' project (playwright.config.ts), reusing the
// demo session auth.setup.ts already established.
test('sending a tutor question gets a real AI-generated reply', async ({ page }) => {
  await page.goto('/')

  const input = page.getByPlaceholder(/ask anything from/i)
  await input.fill('In one sentence, what is a linked list?')

  const [response] = await Promise.all([
    page.waitForResponse((res) => res.url().includes('/chat/ask') && res.status() === 200, {
      timeout: 30_000,
    }),
    page.getByRole('button', { name: /send/i }).click(),
  ])

  const body = (await response.json()) as { reply: string }
  expect(body.reply.length).toBeGreaterThan(10)

  // And that the real reply actually rendered, not just that the API call
  // succeeded — confirms the frontend->backend->OpenAI->backend->frontend
  // round trip end to end, not just half of it.
  await expect(page.getByText(body.reply.slice(0, 30), { exact: false })).toBeVisible()
})
