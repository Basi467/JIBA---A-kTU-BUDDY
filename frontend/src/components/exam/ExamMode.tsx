import { motion } from 'framer-motion'
import { CalendarClock, ChevronRight, LayoutGrid, Loader2, PenLine, Sparkles, Target } from 'lucide-react'
import { useState } from 'react'
import { progressApi, studyPlanApi } from '../../api/endpoints'
import type { StudyPlanItem } from '../../types'
import StudyPlanList from '../StudyPlanList'
import Overview from './Overview'
import TeachHighPriority from './TeachHighPriority'
import SolveRepeatedPyqs from './SolveRepeatedPyqs'

type Tab = 'overview' | 'teach' | 'pyq'

const TABS: { key: Tab; label: string; icon: typeof LayoutGrid }[] = [
  { key: 'overview', label: 'Overview', icon: LayoutGrid },
  { key: 'teach', label: 'Teach High Priority', icon: Target },
  { key: 'pyq', label: 'Solve Repeated PYQs', icon: PenLine },
]

function todayPlusDays(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

function QuickStudyPlan({ subject, hoursPerDay }: { subject: string; hoursPerDay: number }) {
  const [open, setOpen] = useState(false)
  const [examDate, setExamDate] = useState(todayPlusDays(7))
  const [plan, setPlan] = useState<StudyPlanItem[] | null>(null)
  const [loading, setLoading] = useState(false)

  async function generate() {
    setLoading(true)
    try {
      const weak = await progressApi.get(subject).then((p) => p.weak)
      const result = await studyPlanApi.generate(subject, examDate, hoursPerDay, weak)
      setPlan(result)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card-elevated rounded-xl border border-border bg-surface">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium text-text"
      >
        <span className="flex items-center gap-2">
          <CalendarClock size={15} className="text-accent-2" />
          Quick Study Plan
        </span>
        <motion.span animate={{ rotate: open ? 90 : 0 }} className="text-text-muted">
          <ChevronRight size={15} />
        </motion.span>
      </button>

      {open && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          className="space-y-3 overflow-hidden px-4 pb-4"
        >
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="mb-1 block text-xs text-text-muted">Exam Date</label>
              <input
                type="date"
                value={examDate}
                onChange={(e) => setExamDate(e.target.value)}
                className="rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text"
              />
            </div>
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={generate}
              disabled={loading}
              className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-accent-hover disabled:opacity-60"
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
              {loading ? 'Generating...' : 'Generate Study Plan'}
            </motion.button>
          </div>

          {plan && <StudyPlanList plan={plan} />}
        </motion.div>
      )}
    </div>
  )
}

export default function ExamMode({
  subject,
  hoursPerDay,
  onProgressChange,
}: {
  subject: string
  hoursPerDay: number
  onProgressChange: () => void
}) {
  const [tab, setTab] = useState<Tab>('overview')

  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-display text-xl font-bold text-text">Exam Mode</h2>
        <p className="text-sm text-text-muted">
          Module-wise important topics, repeated questions, and guided exam prep.
        </p>
      </div>

      <QuickStudyPlan subject={subject} hoursPerDay={hoursPerDay} />

      <div className="flex gap-1 rounded-xl border border-border bg-surface p-1">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`relative flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              tab === t.key ? 'text-white' : 'text-text-muted hover:text-text'
            }`}
          >
            {tab === t.key && (
              <motion.div layoutId="exam-tab-bg" className="absolute inset-0 rounded-lg bg-accent" />
            )}
            <t.icon size={14} className="relative shrink-0" />
            <span className="relative hidden sm:inline">{t.label}</span>
          </button>
        ))}
      </div>

      <motion.div
        key={tab}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        {tab === 'overview' && <Overview subject={subject} onProgressChange={onProgressChange} />}
        {tab === 'teach' && <TeachHighPriority subject={subject} onProgressChange={onProgressChange} />}
        {tab === 'pyq' && <SolveRepeatedPyqs subject={subject} onProgressChange={onProgressChange} />}
      </motion.div>
    </div>
  )
}
