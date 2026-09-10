import { motion } from 'framer-motion'
import { ChevronRight } from 'lucide-react'
import { useEffect, useState } from 'react'
import { progressApi } from '../api/endpoints'
import type { ProgressSummary } from '../types'

function Collapsible({
  title,
  count,
  items,
  emptyText,
  defaultOpen = false,
}: {
  title: string
  count: number
  items: string[]
  emptyText: string
  defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="rounded-lg border border-border bg-surface">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-3 py-2.5 text-sm font-medium text-text"
      >
        <span>
          {title} <span className="tabular-nums text-text-muted">({count})</span>
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
          {items.length === 0 ? (
            <p className="text-xs text-text-faint">{emptyText}</p>
          ) : (
            <ul className="space-y-1.5">
              {items.slice(0, 10).map((item) => (
                <li key={item} className="rounded-md bg-surface-2 px-2.5 py-1.5 text-xs text-text">
                  {item}
                </li>
              ))}
            </ul>
          )}
        </motion.div>
      )}
    </div>
  )
}

export default function ProgressPanel({ subject, refreshKey }: { subject: string; refreshKey: number }) {
  const [progress, setProgress] = useState<ProgressSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!subject) return
    setLoading(true)
    progressApi
      .get(subject)
      .then(setProgress)
      .finally(() => setLoading(false))
  }, [subject, refreshKey])

  if (loading || !progress) {
    return <div className="h-40 animate-pulse rounded-xl bg-surface" />
  }

  const percent = Math.round(progress.progress_ratio * 100)

  return (
    <div className="space-y-4">
      <div className="card-elevated rounded-xl border border-border bg-surface p-4">
        <h3 className="mb-2.5 text-sm font-semibold text-text">Progress</h3>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-2">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${percent}%` }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="h-full rounded-full bg-gradient-to-r from-accent-2 to-accent"
          />
        </div>
        <p className="tabular-nums mt-1.5 text-xs text-text-muted">{percent}% completed</p>

        <div className="mt-4 grid grid-cols-3 gap-2">
          <Stat label="Weak" value={progress.weak.length} tone="accent" />
          <Stat label="Done" value={progress.completed.length} tone="success" />
          <Stat label="Active" value={progress.in_progress.length} tone="accent-2" />
        </div>
      </div>

      <div className="space-y-2">
        <Collapsible
          title="Weak Topics"
          count={progress.weak.length}
          items={progress.weak}
          emptyText="No weak topics yet."
          defaultOpen
        />
        <Collapsible
          title="Completed Topics"
          count={progress.completed.length}
          items={progress.completed}
          emptyText="No completed topics yet."
        />
        <Collapsible
          title="In Progress"
          count={progress.in_progress.length}
          items={progress.in_progress}
          emptyText="No active topics yet."
        />
      </div>
    </div>
  )
}

function Stat({ label, value, tone }: { label: string; value: number; tone: 'accent' | 'success' | 'accent-2' }) {
  const toneClass = tone === 'accent' ? 'text-accent' : tone === 'success' ? 'text-success' : 'text-accent-2'
  return (
    <div className="rounded-lg border border-border bg-surface-2 py-2 text-center">
      <p className={`tabular-nums text-lg font-bold ${toneClass}`}>{value}</p>
      <p className="text-[11px] text-text-muted">{label}</p>
    </div>
  )
}
