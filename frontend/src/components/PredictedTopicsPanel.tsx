import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { ChevronRight, Target } from 'lucide-react'
import { useState } from 'react'
import { priorityApi } from '../api/endpoints'
import type { ModuleTopicPriority } from '../types'

export default function PredictedTopicsPanel({ subject }: { subject: string }) {
  const [open, setOpen] = useState(false)
  const { data: items = [], isLoading: loading } = useQuery({
    queryKey: ['priority', subject],
    queryFn: () => priorityApi.predicted(subject),
    enabled: !!subject,
  })

  const highPriority = items.filter((i) => i.priority_label === 'High')

  const grouped = highPriority.reduce<Record<number, ModuleTopicPriority[]>>((acc, item) => {
    acc[item.module_no] = acc[item.module_no] ?? []
    acc[item.module_no].push(item)
    return acc
  }, {})

  return (
    <div className="rounded-lg border border-border bg-surface">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-3 py-2.5 text-sm font-medium text-text"
      >
        <span className="flex items-center gap-2">
          <Target size={14} className="text-accent" />
          Predicted High-Priority Topics
        </span>
        <motion.span animate={{ rotate: open ? 90 : 0 }} className="text-text-muted">
          <ChevronRight size={14} />
        </motion.span>
      </button>

      {open && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          className="overflow-hidden px-3 pb-3"
        >
          {loading ? (
            <p className="text-xs text-text-muted">Loading...</p>
          ) : highPriority.length === 0 ? (
            <p className="text-xs text-text-faint">Not enough past-year question data for this subject yet.</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(grouped)
                .slice(0, 5)
                .map(([moduleNo, topics]) => (
                  <div key={moduleNo}>
                    <p className="mb-1 text-xs font-semibold text-accent-2">Module {moduleNo}</p>
                    <ul className="space-y-1">
                      {topics.slice(0, 5).map((t) => (
                        <li
                          key={t.topic_name}
                          className="flex items-center justify-between rounded-md bg-surface-2 px-2.5 py-1.5 text-xs text-text"
                        >
                          <span>{t.topic_name}</span>
                          <span className="tabular-nums text-text-muted">asked {t.question_count}x</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}
