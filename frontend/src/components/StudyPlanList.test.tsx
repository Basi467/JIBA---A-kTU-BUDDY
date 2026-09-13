import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { StudyPlanItem } from '../types'
import StudyPlanList from './StudyPlanList'

function item(overrides: Partial<StudyPlanItem>): StudyPlanItem {
  return {
    plan_date: '2026-01-01',
    subject_name: 'Data Structures',
    module_no: 1,
    topic_id: 1,
    topic_name: 'Linked Lists',
    priority_label: 'High',
    question_count: 3,
    weighted_score: 5,
    recommended_hours: 2,
    priority_score: 5,
    ...overrides,
  }
}

describe('StudyPlanList', () => {
  it('groups items under their module heading', () => {
    render(
      <StudyPlanList
        plan={[item({ module_no: 1, topic_name: 'Linked Lists' }), item({ module_no: 2, topic_name: 'Trees' })]}
      />,
    )

    expect(screen.getByText('Module 1')).toBeInTheDocument()
    expect(screen.getByText('Module 2')).toBeInTheDocument()
    expect(screen.getByText(/Linked Lists/)).toBeInTheDocument()
    expect(screen.getByText(/Trees/)).toBeInTheDocument()
  })

  it('renders date, priority, repeat count, and recommended hours for each item', () => {
    render(
      <StudyPlanList
        plan={[
          item({
            plan_date: '2026-03-15',
            topic_name: 'Linked Lists',
            priority_label: 'High',
            question_count: 4,
            recommended_hours: 2.5,
          }),
        ]}
      />,
    )

    expect(screen.getByText(/2026-03-15/)).toBeInTheDocument()
    expect(screen.getByText(/High, repeated 4x, 2\.5h/)).toBeInTheDocument()
  })

  it('respects the limit prop', () => {
    const plan = [
      item({ module_no: 1, topic_name: 'Topic A' }),
      item({ module_no: 1, topic_name: 'Topic B' }),
      item({ module_no: 1, topic_name: 'Topic C' }),
    ]
    render(<StudyPlanList plan={plan} limit={2} />)

    expect(screen.getByText(/Topic A/)).toBeInTheDocument()
    expect(screen.getByText(/Topic B/)).toBeInTheDocument()
    expect(screen.queryByText(/Topic C/)).not.toBeInTheDocument()
  })
})
