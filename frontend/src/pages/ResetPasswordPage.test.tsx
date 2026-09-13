import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { server } from '../test/server'
import ResetPasswordPage from './ResetPasswordPage'

function renderPage(path = '/reset-password?token=abc123') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <ResetPasswordPage />
    </MemoryRouter>,
  )
}

describe('ResetPasswordPage', () => {
  it('shows a missing-token message when the URL has no token', () => {
    renderPage('/reset-password')
    expect(
      screen.getByText('This reset link is missing its token. Request a new one from the login page.'),
    ).toBeInTheDocument()
    expect(screen.queryByLabelText('New password')).not.toBeInTheDocument()
  })

  it('renders the password form when a token is present', () => {
    renderPage()
    expect(screen.getByLabelText('New password')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirm password')).toBeInTheDocument()
  })

  it('rejects a password shorter than 6 characters without hitting the network', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('New password'), 'abc')
    await user.type(screen.getByLabelText('Confirm password'), 'abc')
    await user.click(screen.getByRole('button', { name: /update password/i }))

    expect(await screen.findByText('Password must be at least 6 characters.')).toBeInTheDocument()
  })

  it('rejects a password/confirm mismatch', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('New password'), 'password1')
    await user.type(screen.getByLabelText('Confirm password'), 'password2')
    await user.click(screen.getByRole('button', { name: /update password/i }))

    expect(await screen.findByText('Passwords do not match.')).toBeInTheDocument()
  })

  it('shows a success message after a valid reset', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('New password'), 'newpassword1')
    await user.type(screen.getByLabelText('Confirm password'), 'newpassword1')
    await user.click(screen.getByRole('button', { name: /update password/i }))

    expect(await screen.findByText('Password updated. You can now log in.')).toBeInTheDocument()
  })

  it('shows the server error for an invalid or expired token', async () => {
    server.use(
      http.post('http://localhost:8000/auth/reset-password', () =>
        HttpResponse.json(
          { detail: 'This reset link is invalid or has expired. Request a new one.' },
          { status: 400 },
        ),
      ),
    )
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('New password'), 'newpassword1')
    await user.type(screen.getByLabelText('Confirm password'), 'newpassword1')
    await user.click(screen.getByRole('button', { name: /update password/i }))

    expect(
      await screen.findByText('This reset link is invalid or has expired. Request a new one.'),
    ).toBeInTheDocument()
  })
})
