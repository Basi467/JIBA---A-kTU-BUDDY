import '@testing-library/jest-dom/vitest'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { server } from './server'

// jsdom doesn't implement scrollIntoView; TutorChat calls it on every
// message update to auto-scroll the chat window.
Element.prototype.scrollIntoView = () => {}

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
afterEach(() => {
  server.resetHandlers()
  localStorage.clear()
})
afterAll(() => server.close())
