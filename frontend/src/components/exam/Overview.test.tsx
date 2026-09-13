import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { ToastProvider } from '../../context/ToastContext'
import { server } from '../../test/server'
import Overview from './Overview'

function renderOverview() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <Overview subject="Data Structures" />
      </ToastProvider>
    </QueryClientProvider>,
  )
}

describe('Overview', () => {
  it('renders module priority columns and repeated questions from real seeded data', async () => {
    renderOverview()

    expect(await screen.findByText('Module 1')).toBeInTheDocument()
    expect(screen.getByText('Linked Lists')).toBeInTheDocument()
    expect(screen.getByText('Arrays')).toBeInTheDocument()
    expect(screen.getByText(/Explain linked lists\./)).toBeInTheDocument()
    expect(screen.getByText('[2024] (10 marks)', { exact: false })).toBeInTheDocument()
  })

  it('shows an empty state when there is no exam data for the subject', async () => {
    server.use(http.get('http://localhost:8000/exam/overview', () => HttpResponse.json([])))
    renderOverview()

    expect(await screen.findByText(/No exam data available for Data Structures yet\./)).toBeInTheDocument()
  })

  it('marks a repeated question as solved and shows a success toast', async () => {
    const user = userEvent.setup()
    renderOverview()

    await screen.findByText('Module 1')
    await user.click(screen.getByRole('button', { name: /solved/i }))

    expect(await screen.findByText('Marked "Linked Lists" as solved')).toBeInTheDocument()
  })

  it('shows an error toast when marking progress fails', async () => {
    server.use(
      http.post('http://localhost:8000/progress/mark', () =>
        HttpResponse.json({ detail: 'Topic not found' }, { status: 404 }),
      ),
    )
    const user = userEvent.setup()
    renderOverview()

    await screen.findByText('Module 1')
    await user.click(screen.getByRole('button', { name: /weak/i }))

    expect(await screen.findByText('Could not update progress. Try again.')).toBeInTheDocument()
  })
})
