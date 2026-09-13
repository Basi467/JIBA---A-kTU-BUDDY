import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import InsightsPanel from './InsightsPanel'

function renderInsightsPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <InsightsPanel subject="Data Structures" />
    </QueryClientProvider>,
  )
}

describe('InsightsPanel', () => {
  it('renders the heading and both progress and predicted-topics panels', async () => {
    renderInsightsPanel()

    expect(screen.getByRole('heading', { name: 'Insights' })).toBeInTheDocument()
    expect(await screen.findByText('Progress')).toBeInTheDocument()
    expect(screen.getByText('Predicted High-Priority Topics')).toBeInTheDocument()
  })
})
