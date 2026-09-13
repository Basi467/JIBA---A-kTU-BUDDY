import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { server } from '../test/server'
import ForgotPasswordPage from './ForgotPasswordPage'

function renderPage() {
  return render(
    <MemoryRouter>
      <ForgotPasswordPage />
    </MemoryRouter>,
  )
}

describe('ForgotPasswordPage', () => {
  it('renders the email field and a link back to login', () => {
    renderPage()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /back to login/i })).toHaveAttribute('href', '/login')
  })

  it('shows the generic success message after submitting', async () => {
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('Email'), 'someone@example.com')
    await user.click(screen.getByRole('button', { name: /send reset link/i }))

    expect(
      await screen.findByText('If that email is registered, a password reset link has been sent.'),
    ).toBeInTheDocument()
    expect(screen.queryByLabelText('Email')).not.toBeInTheDocument()
  })

  it('shows an error message when the request fails', async () => {
    server.use(
      http.post('http://localhost:8000/auth/forgot-password', () =>
        HttpResponse.json({ detail: 'Too many requests. Please slow down and try again shortly.' }, { status: 429 }),
      ),
    )
    const user = userEvent.setup()
    renderPage()

    await user.type(screen.getByLabelText('Email'), 'someone@example.com')
    await user.click(screen.getByRole('button', { name: /send reset link/i }))

    expect(
      await screen.findByText('Too many requests. Please slow down and try again shortly.'),
    ).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
  })
})
