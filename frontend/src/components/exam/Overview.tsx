import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, FileQuestion, Inbox } from 'lucide-react'
import { useEffect, useState } from 'react'
import { examApi, progressApi } from '../../api/endpoints'
import { useToast } from '../../context/ToastContext'
import type { ModuleExamFocus } from '../../types'

const priorityColumns: {
  key: 'high_priority_topics' | 'medium_priority_topics' | 'low_priority_topics'
  label: string
  dot: string
}[] = [
  { key: 'high_priority_topics', label: 'High Priority', dot: 'bg-accent' },
  { key: 'medium_priority_topics', label: 'Medium Priority', dot: 'bg-warning' },
  { key: 'low_priority_topics', label: 'Low Priority', dot: 'bg-text-faint' },
]

export default function Overview({
  subject,
  onProgressChange,
}: {
  subject: string
  onProgressChange: () => void
}) {
  const [modules, setModules] = useState<ModuleExamFocus[]>([])
  const [loading, setLoading] = useState(true)
  const [pendingKey, setPendingKey] = useState<string | null>(null)
  const { showToast } = useToast()

  useEffect(() => {
    setLoading(true)
    examApi
      .overview(subject)
      .then(setModules)
      .finally(() => setLoading(false))
  }, [subject])

  async function handleMark(topic: string, action: 'solved_pyq' | 'weak', key: string) {
    setPendingKey(key)
    try {
      await progressApi.mark(subject, topic, action)
      onProgressChange()
      showToast(
        action === 'solved_pyq' ? `Marked "${topic}" as solved` : `Marked "${topic}" as weak`,
        action === 'solved_pyq' ? 'success' : 'info',
      )
    } catch {
      showToast('Could not update progress. Try again.', 'error')
    } finally {
      setPendingKey(null)
    }
  }

  if (loading) return <div className="h-64 animate-pulse rounded-xl bg-surface" />

  if (modules.length === 0) {
    return (
      <div className="card-elevated flex flex-col items-center gap-2 rounded-2xl border border-border bg-surface/40 px-6 py-12 text-center">
        <Inbox size={22} className="text-text-faint" />
        <p className="text-sm text-text-muted">No exam data available for {subject} yet.</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {modules.map((module) => (
        <motion.div
          key={module.module_no}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-elevated rounded-2xl border border-border bg-surface/40 p-5"
        >
          <h3 className="font-display mb-4 text-lg font-bold text-text">Module {module.module_no}</h3>

          <div className="mb-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
            {priorityColumns.map((col) => (
              <div key={col.key}>
                <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-text-muted">
                  <span className={`h-1.5 w-1.5 rounded-full ${col.dot}`} />
                  {col.label}
                </p>
                {module[col.key].length === 0 ? (
                  <p className="text-xs text-text-faint">None.</p>
                ) : (
                  <ul className="space-y-1">
                    {module[col.key].slice(0, 6).map((t) => (
                      <li key={t} className="rounded-md bg-surface-2 px-2.5 py-1.5 text-xs text-text">
                        {t}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>

          <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-text-muted">
            <FileQuestion size={13} />
            Repeated Questions
          </p>
          {module.repeated_questions.length === 0 ? (
            <p className="text-xs text-text-faint">No repeated questions found.</p>
          ) : (
            <div className="space-y-2">
              {module.repeated_questions.slice(0, 6).map((q, idx) => {
                const key = `${module.module_no}-${idx}`
                return (
                  <div
                    key={key}
                    className="flex items-start justify-between gap-3 rounded-lg border border-border bg-surface p-3 transition-colors hover:border-border-strong"
                  >
                    <div className="flex-1">
                      <p className="text-sm text-text">
                        <span className="tabular-nums font-medium">
                          [{q.year}] ({q.marks} marks)
                        </span>{' '}
                        {q.question_text}
                      </p>
                      {q.topic_name && <p className="mt-1 text-xs text-text-muted">Topic: {q.topic_name}</p>}
                    </div>
                    {q.topic_name && (
                      <div className="flex shrink-0 gap-1.5">
                        <button
                          disabled={pendingKey === key}
                          onClick={() => handleMark(q.topic_name!, 'solved_pyq', key)}
                          className="flex items-center gap-1 rounded-md bg-success/15 px-2.5 py-1 text-xs font-medium text-success transition-colors hover:bg-success/25 disabled:opacity-50"
                        >
                          <CheckCircle2 size={12} />
                          Solved
                        </button>
                        <button
                          disabled={pendingKey === key}
                          onClick={() => handleMark(q.topic_name!, 'weak', key)}
                          className="flex items-center gap-1 rounded-md bg-accent/15 px-2.5 py-1 text-xs font-medium text-accent transition-colors hover:bg-accent/25 disabled:opacity-50"
                        >
                          <AlertTriangle size={12} />
                          Weak
                        </button>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </motion.div>
      ))}
    </div>
  )
}
