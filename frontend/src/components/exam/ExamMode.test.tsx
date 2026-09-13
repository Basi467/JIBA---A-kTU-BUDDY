import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { ToastProvider } from '../../context/ToastContext'
import ExamMode from './ExamMode'

function renderExamMode() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <ExamMode subject="Data Structures" hoursPerDay={3} />
      </ToastProvider>
    </QueryClientProvider>,
  )
}

describe('ExamMode', () => {
  it('renders the heading and all three tabs', () => {
    renderExamMode()
    expect(screen.getByRole('heading', { name: 'Exam Mode' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /overview/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /teach high priority/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /solve repeated pyqs/i })).toBeInTheDocument()
  })

  it('defaults to the Overview tab and shows real seeded exam data', async () => {
    renderExamMode()
    expect(await screen.findByText('Module 1')).toBeInTheDocument()
    expect(screen.getByText('Linked Lists')).toBeInTheDocument()
    expect(screen.getByText(/Explain linked lists\./)).toBeInTheDocument()
  })

  it('switches to the Teach High Priority tab on click', async () => {
    const user = userEvent.setup()
    renderExamMode()

    await user.click(screen.getByRole('button', { name: /teach high priority/i }))

    expect(
      await screen.findByRole('button', { name: /start teaching high priority topics/i }),
    ).toBeInTheDocument()
  })

  it('switches to the Solve Repeated PYQs tab on click', async () => {
    const user = userEvent.setup()
    renderExamMode()

    await user.click(screen.getByRole('button', { name: /solve repeated pyqs/i }))

    expect(
      await screen.findByRole('button', { name: /start solving repeated pyqs/i }),
    ).toBeInTheDocument()
  })

  it('generates a study plan from the Quick Study Plan panel', async () => {
    const user = userEvent.setup()
    renderExamMode()

    await user.click(screen.getByRole('button', { name: /quick study plan/i }))
    await user.click(screen.getByRole('button', { name: /generate study plan/i }))

    expect(await screen.findByText('2026-01-01', { exact: false })).toBeInTheDocument()
  })
})
