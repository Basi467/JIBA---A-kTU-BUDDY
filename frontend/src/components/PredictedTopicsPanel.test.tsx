import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../test/server'
import PredictedTopicsPanel from './PredictedTopicsPanel'

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <PredictedTopicsPanel subject="Data Structures" />
    </QueryClientProvider>,
  )
}

describe('PredictedTopicsPanel', () => {
  it('is collapsed by default', () => {
    renderPanel()
    expect(screen.getByText('Predicted High-Priority Topics')).toBeInTheDocument()
    expect(screen.queryByText(/asked/)).not.toBeInTheDocument()
  })

  it('shows only High-priority topics, grouped by module, once expanded', async () => {
    server.use(
      http.get('http://localhost:8000/priority/predicted', () =>
        HttpResponse.json([
          { subject_name: 'Data Structures', module_no: 1, topic_name: 'Linked Lists', question_count: 4, weighted_score: 5, priority_label: 'High' },
          { subject_name: 'Data Structures', module_no: 1, topic_name: 'Arrays', question_count: 1, weighted_score: 1, priority_label: 'Medium' },
          { subject_name: 'Data Structures', module_no: 2, topic_name: 'Trees', question_count: 2, weighted_score: 3, priority_label: 'High' },
        ]),
      ),
    )
    const user = userEvent.setup()
    renderPanel()

    await user.click(screen.getByRole('button', { name: /predicted high-priority topics/i }))

    expect(await screen.findByText('Linked Lists')).toBeInTheDocument()
    expect(screen.getByText('asked 4x')).toBeInTheDocument()
    expect(screen.getByText('Trees')).toBeInTheDocument()
    expect(screen.getByText('Module 1')).toBeInTheDocument()
    expect(screen.getByText('Module 2')).toBeInTheDocument()
    expect(screen.queryByText('Arrays')).not.toBeInTheDocument()
  })

  it('shows an empty-state message when there are no High-priority topics', async () => {
    server.use(http.get('http://localhost:8000/priority/predicted', () => HttpResponse.json([])))
    const user = userEvent.setup()
    renderPanel()

    await user.click(screen.getByRole('button', { name: /predicted high-priority topics/i }))

    expect(
      await screen.findByText('Not enough past-year question data for this subject yet.'),
    ).toBeInTheDocument()
  })
})
