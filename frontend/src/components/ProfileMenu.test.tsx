import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { setStoredToken } from '../api/client'
import { AuthProvider } from '../context/AuthContext'
import ProfileMenu from './ProfileMenu'

function renderProfileMenu({ withToken = true } = {}) {
  if (withToken) setStoredToken('fake-token')
  return render(
    <AuthProvider>
      <ProfileMenu />
    </AuthProvider>,
  )
}

describe('ProfileMenu', () => {
  it('renders nothing while unauthenticated', () => {
    const { container } = renderProfileMenu({ withToken: false })
    expect(container).toBeEmptyDOMElement()
  })

  it('renders the avatar trigger once the user loads', async () => {
    renderProfileMenu()
    expect(await screen.findByRole('button', { name: 'Account menu for Demo User' })).toHaveTextContent('D')
  })

  it('opens to show the user\'s profile details', async () => {
    const user = userEvent.setup()
    renderProfileMenu()

    await user.click(await screen.findByRole('button', { name: 'Account menu for Demo User' }))

    expect(await screen.findByText('Demo User')).toBeInTheDocument()
    expect(screen.getByText('demo@example.com')).toBeInTheDocument()
    expect(screen.getByText('CSE')).toBeInTheDocument()
    expect(screen.getByText('Sem 3')).toBeInTheDocument()
    expect(screen.getByText('KTU_2019')).toBeInTheDocument()
  })

  it('logging out clears the session and hides the menu', async () => {
    const user = userEvent.setup()
    renderProfileMenu()

    const trigger = await screen.findByRole('button', { name: 'Account menu for Demo User' })
    await user.click(trigger)
    await user.click(await screen.findByText('Logout'))

    expect(screen.queryByRole('button', { name: 'Account menu for Demo User' })).not.toBeInTheDocument()
    expect(localStorage.getItem('jiba_token')).toBeNull()
  })
})
