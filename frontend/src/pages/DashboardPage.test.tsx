import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { afterEach, describe, expect, it } from 'vitest'
import { setStoredToken } from '../api/client'
import { AuthProvider } from '../context/AuthContext'
import { ToastProvider } from '../context/ToastContext'
import { server } from '../test/server'
import DashboardPage from './DashboardPage'

function renderDashboard() {
  setStoredToken('fake-token')
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ToastProvider>
          <DashboardPage />
        </ToastProvider>
      </AuthProvider>
    </QueryClientProvider>,
  )
}

describe('DashboardPage', () => {
  afterEach(() => server.resetHandlers())

  it('loads the default subject and shows the tutor chat empty state', async () => {
    renderDashboard()
    expect(await screen.findByText('Data Structures')).toBeInTheDocument()
    expect(await screen.findByText('Ask your tutor anything')).toBeInTheDocument()
  })

  it('shows a message when the user has no subjects', async () => {
    server.use(http.get('http://localhost:8000/subjects', () => HttpResponse.json([])))
    renderDashboard()
    expect(await screen.findByText('No subjects found for your profile.')).toBeInTheDocument()
  })

  it('switches from tutor chat to exam mode via the toggle', async () => {
    const user = userEvent.setup()
    renderDashboard()

    await screen.findByText('Ask your tutor anything')
    await user.click(screen.getByRole('switch', { name: /toggle exam mode/i }))

    expect(await screen.findByRole('heading', { name: 'Exam Mode' })).toBeInTheDocument()
    expect(screen.queryByText('Ask your tutor anything')).not.toBeInTheDocument()
  })

  it('opens the insights panel with focus on the close button, and Escape closes it with focus restored', async () => {
    const user = userEvent.setup()
    renderDashboard()
    await screen.findByText('Ask your tutor anything')

    const trigger = screen.getByRole('button', { name: /progress & insights/i })
    await user.click(trigger)

    const dialog = await screen.findByRole('dialog', { name: 'Insights' })
    const closeButton = screen.getByRole('button', { name: /close insights/i })
    expect(closeButton).toHaveFocus()

    await user.keyboard('{Escape}')

    expect(dialog).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })
})
