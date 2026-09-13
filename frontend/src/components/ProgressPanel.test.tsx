import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../test/server'
import ProgressPanel from './ProgressPanel'

function renderProgressPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ProgressPanel subject="Data Structures" />
    </QueryClientProvider>,
  )
}

describe('ProgressPanel', () => {
  it('renders the completion percentage and stat counts', async () => {
    server.use(
      http.get('http://localhost:8000/progress', () =>
        HttpResponse.json({
          weak: ['Topic A'],
          completed: ['Topic B', 'Topic C'],
          in_progress: ['Topic D'],
          progress_ratio: 0.5,
        }),
      ),
    )
    renderProgressPanel()

    expect(await screen.findByText('50% completed')).toBeInTheDocument()
    // Stat values: Weak=1, Done=2, Active=1
    const stats = screen.getAllByText(/^[0-9]+$/)
    expect(stats.map((el) => el.textContent)).toEqual(['1', '2', '1'])
  })

  it('shows weak topics expanded by default, others collapsed until clicked', async () => {
    const user = userEvent.setup()
    server.use(
      http.get('http://localhost:8000/progress', () =>
        HttpResponse.json({
          weak: ['Topic A'],
          completed: ['Topic B'],
          in_progress: [],
          progress_ratio: 0.5,
        }),
      ),
    )
    renderProgressPanel()

    expect(await screen.findByText('Topic A')).toBeInTheDocument()
    expect(screen.queryByText('Topic B')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /completed topics/i }))
    expect(await screen.findByText('Topic B')).toBeInTheDocument()
  })

  it('shows the empty-state text for a section with no topics', async () => {
    server.use(
      http.get('http://localhost:8000/progress', () =>
        HttpResponse.json({ weak: [], completed: [], in_progress: [], progress_ratio: 0 }),
      ),
    )
    renderProgressPanel()

    expect(await screen.findByText('No weak topics yet.')).toBeInTheDocument()
  })
})
