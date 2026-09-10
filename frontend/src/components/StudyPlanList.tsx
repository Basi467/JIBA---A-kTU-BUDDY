import type { StudyPlanItem } from '../types'

export default function StudyPlanList({ plan, limit = 20 }: { plan: StudyPlanItem[]; limit?: number }) {
  const grouped = plan.slice(0, limit).reduce<Record<number, StudyPlanItem[]>>((acc, item) => {
    acc[item.module_no] = acc[item.module_no] ?? []
    acc[item.module_no].push(item)
    return acc
  }, {})

  return (
    <div className="space-y-3">
      {Object.entries(grouped).map(([moduleNo, items]) => (
        <div key={moduleNo}>
          <p className="mb-1 text-xs font-semibold text-accent-2">Module {moduleNo}</p>
          <ul className="space-y-1.5">
            {items.map((item, idx) => (
              <li key={idx} className="rounded-md bg-surface-2 px-2.5 py-1.5 text-xs text-text">
                <span className="font-medium">{item.plan_date}</span> — {item.topic_name}{' '}
                <span className="text-text-muted">
                  ({item.priority_label}, repeated {item.question_count}x, {item.recommended_hours}h)
                </span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
