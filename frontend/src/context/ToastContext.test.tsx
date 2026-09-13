import { fireEvent, render, screen, waitForElementToBeRemoved } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ToastProvider, useToast } from './ToastContext'

function TestConsumer() {
  const { showToast } = useToast()
  return (
    <>
      <button onClick={() => showToast('Saved successfully', 'success')}>Show Success</button>
      <button onClick={() => showToast('Something broke', 'error')}>Show Error</button>
      <button onClick={() => showToast('Just so you know', 'info')}>Show Info</button>
    </>
  )
}

function renderWithProvider() {
  return render(
    <ToastProvider>
      <TestConsumer />
    </ToastProvider>,
  )
}

describe('useToast', () => {
  it('throws when used outside a ToastProvider', () => {
    // Suppress the expected React error-boundary console noise for this one.
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<TestConsumer />)).toThrow('useToast must be used within a ToastProvider')
    consoleSpy.mockRestore()
  })
})

describe('ToastProvider', () => {
  it('shows a success toast with role="status"', async () => {
    renderWithProvider()
    fireEvent.click(screen.getByRole('button', { name: 'Show Success' }))

    const toast = await screen.findByRole('status')
    expect(toast).toHaveTextContent('Saved successfully')
  })

  it('shows an error toast with role="alert"', async () => {
    renderWithProvider()
    fireEvent.click(screen.getByRole('button', { name: 'Show Error' }))

    const toast = await screen.findByRole('alert')
    expect(toast).toHaveTextContent('Something broke')
  })

  it('shows an info toast with role="status"', async () => {
    renderWithProvider()
    fireEvent.click(screen.getByRole('button', { name: 'Show Info' }))

    const toast = await screen.findByRole('status')
    expect(toast).toHaveTextContent('Just so you know')
  })

  it('stacks multiple toasts at once', async () => {
    renderWithProvider()
    fireEvent.click(screen.getByRole('button', { name: 'Show Success' }))
    fireEvent.click(screen.getByRole('button', { name: 'Show Error' }))

    expect(await screen.findByText('Saved successfully')).toBeInTheDocument()
    expect(await screen.findByText('Something broke')).toBeInTheDocument()
  })
})

describe('ToastProvider auto-dismiss', () => {
  // Real timers, not fake ones: the toast's exit is a Framer Motion
  // animation driven by requestAnimationFrame, which fake timers freeze —
  // the underlying setTimeout(…, 3000) that triggers removal fires fine
  // under fake time, but AnimatePresence then never sees the animation
  // complete and keeps the node mounted forever. A real (slow) wait avoids
  // fighting that interaction rather than trying to fix it.
  it('removes the toast a few seconds after it appears', async () => {
    renderWithProvider()
    fireEvent.click(screen.getByRole('button', { name: 'Show Success' }))

    const toast = screen.getByText('Saved successfully')
    await waitForElementToBeRemoved(toast, { timeout: 4000 })
  }, 6000)
})
