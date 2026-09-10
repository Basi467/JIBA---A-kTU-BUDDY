import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import ErrorBoundary from './ErrorBoundary'

function Bomb(): never {
  throw new Error('Boom')
}

describe('ErrorBoundary', () => {
  it('renders a fallback UI instead of crashing when a child throws', () => {
    // React logs the thrown error to console.error even when caught by a
    // boundary — silence it so the test output isn't noisy with an
    // intentional, expected error.
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <ErrorBoundary>
        <Bomb />
      </ErrorBoundary>,
    )

    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /reload/i })).toBeInTheDocument()

    consoleSpy.mockRestore()
  })

  it('renders children normally when nothing throws', () => {
    render(
      <ErrorBoundary>
        <div>All good</div>
      </ErrorBoundary>,
    )

    expect(screen.getByText('All good')).toBeInTheDocument()
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
  })
})
