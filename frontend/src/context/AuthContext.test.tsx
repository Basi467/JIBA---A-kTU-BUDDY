import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it, vi } from 'vitest'
import { getStoredToken, setStoredToken } from '../api/client'
import { server } from '../test/server'
import { AuthProvider, useAuth } from './AuthContext'

function TestConsumer() {
  const { user, isLoading, login, logout } = useAuth()
  return (
    <div>
      <p>isLoading: {String(isLoading)}</p>
      <p>user: {user ? user.email : 'none'}</p>
      <button onClick={() => login('demo@example.com', 'correctpass')}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  )
}

function renderWithProvider() {
  return render(
    <AuthProvider>
      <TestConsumer />
    </AuthProvider>,
  )
}

describe('useAuth', () => {
  it('throws when used outside an AuthProvider', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<TestConsumer />)).toThrow('useAuth must be used within an AuthProvider')
    consoleSpy.mockRestore()
  })
})

describe('AuthProvider', () => {
  it('resolves to no user when no token is stored', async () => {
    renderWithProvider()
    expect(await screen.findByText('isLoading: false')).toBeInTheDocument()
    expect(screen.getByText('user: none')).toBeInTheDocument()
  })

  it('loads the user from /auth/me when a token is already stored', async () => {
    setStoredToken('fake-token')
    renderWithProvider()

    expect(await screen.findByText('user: demo@example.com')).toBeInTheDocument()
    expect(screen.getByText('isLoading: false')).toBeInTheDocument()
  })

  it('clears the token when /auth/me rejects it', async () => {
    setStoredToken('a-stale-token')
    server.use(
      http.get('http://localhost:8000/auth/me', () => HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 })),
    )
    renderWithProvider()

    await screen.findByText('isLoading: false')
    expect(screen.getByText('user: none')).toBeInTheDocument()
    expect(getStoredToken()).toBeNull()
  })

  it('login() stores the token and sets the user', async () => {
    const user = userEvent.setup()
    renderWithProvider()
    await screen.findByText('isLoading: false')

    await user.click(screen.getByRole('button', { name: 'Login' }))

    expect(await screen.findByText('user: demo@example.com')).toBeInTheDocument()
    expect(getStoredToken()).toBe('fake-token')
  })

  it('logout() clears the token and the user', async () => {
    const user = userEvent.setup()
    setStoredToken('fake-token')
    renderWithProvider()
    await screen.findByText('user: demo@example.com')

    await user.click(screen.getByRole('button', { name: 'Logout' }))

    expect(await screen.findByText('user: none')).toBeInTheDocument()
    expect(getStoredToken()).toBeNull()
  })
})
