import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import SubjectSwitcher from './SubjectSwitcher'

const SUBJECTS = [
  { subject_code: 'CST205', subject_name: 'Data Structures' },
  { subject_code: 'CST201', subject_name: 'Computer Networks' },
]

describe('SubjectSwitcher', () => {
  it('shows the currently selected subject on the trigger', () => {
    render(<SubjectSwitcher subjects={SUBJECTS} selected="Data Structures" onSelect={() => {}} />)
    expect(screen.getByRole('button', { name: /select subject/i })).toHaveTextContent('Data Structures')
  })

  it('shows a placeholder when nothing is selected', () => {
    render(<SubjectSwitcher subjects={SUBJECTS} selected="" onSelect={() => {}} />)
    expect(screen.getByRole('button', { name: /select subject/i })).toHaveTextContent('Select subject')
  })

  it('opens to show every subject with its code', async () => {
    const user = userEvent.setup()
    render(<SubjectSwitcher subjects={SUBJECTS} selected="Data Structures" onSelect={() => {}} />)

    await user.click(screen.getByRole('button', { name: /select subject/i }))

    expect(await screen.findByText('Computer Networks')).toBeInTheDocument()
    expect(screen.getByText('CST205')).toBeInTheDocument()
    expect(screen.getByText('CST201')).toBeInTheDocument()
  })

  it('filters the list as you type in the search box', async () => {
    const user = userEvent.setup()
    render(<SubjectSwitcher subjects={SUBJECTS} selected="Data Structures" onSelect={() => {}} />)

    await user.click(screen.getByRole('button', { name: /select subject/i }))
    await screen.findByText('Computer Networks')

    await user.type(screen.getByRole('textbox', { name: /search subjects/i }), 'network')

    expect(screen.getByText('Computer Networks')).toBeInTheDocument()
    expect(screen.queryByText('CST205')).not.toBeInTheDocument()
  })

  it('shows a no-match message when the search matches nothing', async () => {
    const user = userEvent.setup()
    render(<SubjectSwitcher subjects={SUBJECTS} selected="Data Structures" onSelect={() => {}} />)

    await user.click(screen.getByRole('button', { name: /select subject/i }))
    await user.type(screen.getByRole('textbox', { name: /search subjects/i }), 'nonexistent subject')

    expect(await screen.findByText('No subjects match.')).toBeInTheDocument()
  })

  it('calls onSelect with the subject name and closes the popover on click', async () => {
    const user = userEvent.setup()
    const onSelect = vi.fn()
    render(<SubjectSwitcher subjects={SUBJECTS} selected="Data Structures" onSelect={onSelect} />)

    await user.click(screen.getByRole('button', { name: /select subject/i }))
    await user.click(await screen.findByText('Computer Networks'))

    expect(onSelect).toHaveBeenCalledWith('Computer Networks')
    expect(screen.queryByRole('textbox', { name: /search subjects/i })).not.toBeInTheDocument()
  })
})
