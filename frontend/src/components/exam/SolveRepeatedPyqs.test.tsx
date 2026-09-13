import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { ToastProvider } from '../../context/ToastContext'
import SolveRepeatedPyqs from './SolveRepeatedPyqs'

function renderSolveRepeatedPyqs() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <SolveRepeatedPyqs subject="Data Structures" />
      </ToastProvider>
    </QueryClientProvider>,
  )
}

describe('SolveRepeatedPyqs', () => {
  it('shows the start screen before the queue is started', () => {
    renderSolveRepeatedPyqs()
    expect(screen.getByRole('button', { name: /start solving repeated pyqs/i })).toBeInTheDocument()
  })

  it('loads the queue and the mocked answer on start', async () => {
    const user = userEvent.setup()
    renderSolveRepeatedPyqs()

    await user.click(screen.getByRole('button', { name: /start solving repeated pyqs/i }))

    expect(await screen.findByText('Explain linked lists.')).toBeInTheDocument()
    expect(screen.getByText(/Topic: Linked Lists/)).toBeInTheDocument()
    expect(await screen.findByText('A mocked answer.')).toBeInTheDocument()
  })

  it('marking the only question solved completes the queue', async () => {
    const user = userEvent.setup()
    renderSolveRepeatedPyqs()

    await user.click(screen.getByRole('button', { name: /start solving repeated pyqs/i }))
    await screen.findByText('A mocked answer.')

    await user.click(screen.getByRole('button', { name: /^solved$/i }))

    expect(
      await screen.findByText('You completed all repeated-question practice items.'),
    ).toBeInTheDocument()
    expect(await screen.findByText('Nice — marked as solved')).toBeInTheDocument()
  })

  it('restarting the queue after completion shows the first question again', async () => {
    const user = userEvent.setup()
    renderSolveRepeatedPyqs()

    await user.click(screen.getByRole('button', { name: /start solving repeated pyqs/i }))
    await screen.findByText('A mocked answer.')
    await user.click(screen.getByRole('button', { name: /^solved$/i }))
    await screen.findByText('You completed all repeated-question practice items.')

    await user.click(screen.getByRole('button', { name: /restart pyq queue/i }))

    expect(await screen.findByText('Explain linked lists.')).toBeInTheDocument()
  })
})
