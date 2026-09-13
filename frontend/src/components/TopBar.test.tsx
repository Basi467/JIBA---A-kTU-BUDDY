import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ComponentProps } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { setStoredToken } from '../api/client'
import { AuthProvider } from '../context/AuthContext'
import TopBar from './TopBar'

const SUBJECTS = [{ subject_code: 'CST205', subject_name: 'Data Structures' }]

function renderTopBar(overrides: Partial<ComponentProps<typeof TopBar>> = {}) {
  setStoredToken('fake-token')
  const props: ComponentProps<typeof TopBar> = {
    subjects: SUBJECTS,
    selectedSubject: 'Data Structures',
    onSelectSubject: vi.fn(),
    examMode: false,
    onToggleExamMode: vi.fn(),
    hoursPerDay: 3,
    onChangeHoursPerDay: vi.fn(),
    onOpenInsights: vi.fn(),
    ...overrides,
  }
  return { props, ...render(<AuthProvider><TopBar {...props} /></AuthProvider>) }
}

describe('TopBar', () => {
  it('renders the logo, subject switcher, and profile menu', async () => {
    renderTopBar()
    expect(screen.getByText('JIBA')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /select subject/i })).toHaveTextContent('Data Structures')
    expect(await screen.findByRole('button', { name: 'Account menu for Demo User' })).toBeInTheDocument()
  })

  it('reflects the examMode prop on the toggle switch', () => {
    const { rerender, props } = renderTopBar({ examMode: false })
    expect(screen.getByRole('switch', { name: /toggle exam mode/i })).toHaveAttribute('aria-checked', 'false')

    rerender(
      <AuthProvider>
        <TopBar {...props} examMode />
      </AuthProvider>,
    )
    expect(screen.getByRole('switch', { name: /toggle exam mode/i })).toHaveAttribute('aria-checked', 'true')
  })

  it('calls onToggleExamMode with the flipped value on click', async () => {
    const user = userEvent.setup()
    const { props } = renderTopBar({ examMode: false })

    await user.click(screen.getByRole('switch', { name: /toggle exam mode/i }))

    expect(props.onToggleExamMode).toHaveBeenCalledWith(true)
  })

  it('opens study settings showing the current hours-per-day value', async () => {
    const user = userEvent.setup()
    renderTopBar({ hoursPerDay: 5 })

    await user.click(screen.getByRole('button', { name: /study settings/i }))

    expect(await screen.findByText('5h / day')).toBeInTheDocument()
    expect(screen.getByLabelText('Hours per day')).toHaveValue('5')
  })

  it('calls onOpenInsights when the insights button is clicked', async () => {
    const user = userEvent.setup()
    const { props } = renderTopBar()

    await user.click(screen.getByRole('button', { name: /progress & insights/i }))

    expect(props.onOpenInsights).toHaveBeenCalledTimes(1)
  })

  it('omits the insights button when onOpenInsights is not provided', () => {
    renderTopBar({ onOpenInsights: undefined })
    expect(screen.queryByRole('button', { name: /progress & insights/i })).not.toBeInTheDocument()
  })
})
