import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import App from './App'
import { setStoredToken } from './api/client'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'

function renderApp(initialPath: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialPath]}>
        <AuthProvider>
          <ToastProvider>
            <App />
          </ToastProvider>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('App routing', () => {
  it('redirects an unauthenticated visitor from / to the login page', async () => {
    renderApp('/')
    expect(await screen.findByText('Welcome back')).toBeInTheDocument()
  })

  it('redirects an authenticated visitor away from /login to the dashboard', async () => {
    setStoredToken('fake-token')
    renderApp('/login')
    expect(await screen.findByText('Data Structures')).toBeInTheDocument()
    expect(screen.queryByText('Welcome back')).not.toBeInTheDocument()
  })

  it('lets an authenticated visitor reach the dashboard directly at /', async () => {
    setStoredToken('fake-token')
    renderApp('/')
    expect(await screen.findByText('Ask your tutor anything')).toBeInTheDocument()
  })

  it('redirects an unknown path to / (and on to login when unauthenticated)', async () => {
    renderApp('/some-nonexistent-path')
    expect(await screen.findByText('Welcome back')).toBeInTheDocument()
  })

  it('serves the forgot-password page without requiring authentication', async () => {
    renderApp('/forgot-password')
    expect(await screen.findByText('Reset your password')).toBeInTheDocument()
  })

  it('serves the reset-password page without requiring authentication', async () => {
    renderApp('/reset-password?token=abc123')
    expect(await screen.findByText('Choose a new password')).toBeInTheDocument()
  })
})
