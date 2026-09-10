import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { setStoredToken } from '../api/client'
import { AuthProvider } from '../context/AuthContext'
import ProtectedRoute from './ProtectedRoute'

function renderProtected() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <div>Secret Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  it('redirects to /login when no token is stored', async () => {
    renderProtected()
    expect(await screen.findByText('Login Page')).toBeInTheDocument()
  })

  it('renders children when a valid token resolves to a user', async () => {
    setStoredToken('fake-token')
    renderProtected()
    expect(await screen.findByText('Secret Content')).toBeInTheDocument()
  })
})
