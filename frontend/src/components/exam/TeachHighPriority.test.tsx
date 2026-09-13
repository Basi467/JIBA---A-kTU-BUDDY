import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { ToastProvider } from '../../context/ToastContext'
import TeachHighPriority from './TeachHighPriority'

function renderTeachHighPriority() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <TeachHighPriority subject="Data Structures" />
      </ToastProvider>
    </QueryClientProvider>,
  )
}

describe('TeachHighPriority', () => {
  it('shows the start screen before the queue is started', () => {
    renderTeachHighPriority()
    expect(screen.getByRole('button', { name: /start teaching high priority topics/i })).toBeInTheDocument()
  })

  it('loads the queue and the mocked lesson content on start', async () => {
    const user = userEvent.setup()
    renderTeachHighPriority()

    await user.click(screen.getByRole('button', { name: /start teaching high priority topics/i }))

    expect(await screen.findByRole('heading', { name: 'Linked Lists' })).toBeInTheDocument()
    expect(screen.getByText(/Module 1/)).toBeInTheDocument()
    expect(await screen.findByText('A mocked simple explanation.')).toBeInTheDocument()
    expect(screen.getByText('A mocked exam answer.')).toBeInTheDocument()
    expect(screen.getByText('Point one')).toBeInTheDocument()
    expect(screen.getByText('A mocked memory tip.')).toBeInTheDocument()
    expect(screen.getByText('A mocked practice question?')).toBeInTheDocument()
  })

  it('marking the only topic done completes the queue', async () => {
    const user = userEvent.setup()
    renderTeachHighPriority()

    await user.click(screen.getByRole('button', { name: /start teaching high priority topics/i }))
    await screen.findByRole('heading', { name: 'Linked Lists' })

    await user.click(screen.getByRole('button', { name: /^done$/i }))

    expect(await screen.findByText('You completed all high-priority topics.')).toBeInTheDocument()
    expect(await screen.findByText('"Linked Lists" marked done')).toBeInTheDocument()
  })

  it('restarting the queue after completion shows the first topic again', async () => {
    const user = userEvent.setup()
    renderTeachHighPriority()

    await user.click(screen.getByRole('button', { name: /start teaching high priority topics/i }))
    await screen.findByRole('heading', { name: 'Linked Lists' })
    await user.click(screen.getByRole('button', { name: /^done$/i }))
    await screen.findByText('You completed all high-priority topics.')

    await user.click(screen.getByRole('button', { name: /restart teaching queue/i }))

    expect(await screen.findByRole('heading', { name: 'Linked Lists' })).toBeInTheDocument()
  })
})
