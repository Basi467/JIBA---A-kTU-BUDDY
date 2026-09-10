import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import TutorChat from './TutorChat'

function renderTutorChat() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <TutorChat subject="Data Structures" hoursPerDay={3} />
    </QueryClientProvider>,
  )
}

describe('TutorChat', () => {
  it('shows the empty state with suggested prompts once history loads empty', async () => {
    renderTutorChat()
    expect(await screen.findByText('Ask your tutor anything')).toBeInTheDocument()
    expect(screen.getByText('What are the most important topics?')).toBeInTheDocument()
  })

  it('sends a question and renders the mocked assistant reply', async () => {
    const user = userEvent.setup()
    renderTutorChat()

    await screen.findByText('Ask your tutor anything')

    const input = screen.getByPlaceholderText('Ask anything from Data Structures')
    await user.type(input, 'What is a linked list?')
    await user.click(screen.getByRole('button', { name: /send/i }))

    expect(await screen.findByText('This is a mocked tutor reply.')).toBeInTheDocument()
    expect(screen.getByText('What is a linked list?')).toBeInTheDocument()
  })
})
