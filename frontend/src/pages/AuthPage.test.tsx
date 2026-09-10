import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AuthProvider } from '../context/AuthContext'
import AuthPage from './AuthPage'

function renderAuthPage() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<AuthPage />} />
          <Route path="/" element={<div>Dashboard Placeholder</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('AuthPage login', () => {
  it('shows an error on invalid credentials', async () => {
    const user = userEvent.setup()
    renderAuthPage()

    await user.type(screen.getByLabelText('Email'), 'demo@example.com')
    await user.type(screen.getByLabelText('Password'), 'wrongpassword')
    await user.click(screen.getByRole('button', { name: 'Login' }))

    expect(await screen.findByText('Invalid email or password')).toBeInTheDocument()
    expect(screen.queryByText('Dashboard Placeholder')).not.toBeInTheDocument()
  })

  it('navigates to / on successful login', async () => {
    const user = userEvent.setup()
    renderAuthPage()

    await user.type(screen.getByLabelText('Email'), 'demo@example.com')
    await user.type(screen.getByLabelText('Password'), 'correctpass')
    await user.click(screen.getByRole('button', { name: 'Login' }))

    expect(await screen.findByText('Dashboard Placeholder')).toBeInTheDocument()
  })

  it('has a Forgot password? link pointing to /forgot-password', () => {
    renderAuthPage()
    expect(screen.getByRole('link', { name: /forgot password/i })).toHaveAttribute(
      'href',
      '/forgot-password',
    )
  })
})

describe('AuthPage register', () => {
  it('rejects a password/confirm mismatch without hitting the network', async () => {
    const user = userEvent.setup()
    renderAuthPage()

    await user.click(screen.getByRole('button', { name: /^register$/i }))

    await user.type(screen.getByLabelText('Full Name'), 'Test Student')
    await user.type(screen.getByLabelText('Email'), 'new.student@example.com')
    await user.type(screen.getByLabelText('Password'), 'password1')
    await user.type(screen.getByLabelText('Confirm'), 'password2')

    await waitFor(() => expect(screen.getByLabelText('Scheme')).toBeEnabled())
    await user.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByText('Passwords do not match.')).toBeInTheDocument()
  })

  it('loads scheme/department/semester options from the signup-options endpoint', async () => {
    const user = userEvent.setup()
    renderAuthPage()

    await user.click(screen.getByRole('button', { name: /^register$/i }))

    expect(await screen.findByRole('option', { name: 'CSE' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'KTU_2019' })).toBeInTheDocument()
  })
})
