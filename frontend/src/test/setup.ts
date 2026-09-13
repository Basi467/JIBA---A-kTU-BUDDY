import '@testing-library/jest-dom/vitest'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { server } from './server'

// jsdom doesn't implement scrollIntoView/scrollTo; TutorChat and Radix
// UI's Popover/Dropdown call these when scrolling content into view.
Element.prototype.scrollIntoView = () => {}
window.scrollTo = () => {}

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
afterEach(() => {
  server.resetHandlers()
  localStorage.clear()
})
afterAll(() => server.close())
