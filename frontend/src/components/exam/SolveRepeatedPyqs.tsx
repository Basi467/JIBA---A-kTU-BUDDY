import { motion } from 'framer-motion'
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Loader2,
  PenLine,
  RotateCcw,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { examApi, progressApi } from '../../api/endpoints'
import { useToast } from '../../context/ToastContext'
import Markdown from '../Markdown'
import type { TeachQuestionItem } from '../../types'

export default function SolveRepeatedPyqs({
  subject,
  onProgressChange,
}: {
  subject: string
  onProgressChange: () => void
}) {
  const [queue, setQueue] = useState<TeachQuestionItem[] | null>(null)
  const [index, setIndex] = useState(0)
  const [answer, setAnswer] = useState<string | null>(null)
  const [loadingAnswer, setLoadingAnswer] = useState(false)
  const [starting, setStarting] = useState(false)
  const [marking, setMarking] = useState(false)
  const { showToast } = useToast()

  useEffect(() => {
    setQueue(null)
    setIndex(0)
    setAnswer(null)
  }, [subject])

  const current = queue && index < queue.length ? queue[index] : null

  useEffect(() => {
    if (!current) return
    setLoadingAnswer(true)
    setAnswer(null)
    examApi
      .answerQuestion(subject, current.question_text, current.topic_name)
      .then(setAnswer)
      .finally(() => setLoadingAnswer(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index, current?.question_text])

  async function start() {
    setStarting(true)
    try {
      const items = await examApi.pyqQueue(subject, 4)
      setQueue(items)
      setIndex(0)
    } finally {
      setStarting(false)
    }
  }

  async function mark(action: 'solved_pyq' | 'weak') {
    if (!current?.topic_name) {
      setIndex((i) => i + 1)
      return
    }
    setMarking(true)
    try {
      await progressApi.mark(subject, current.topic_name, action)
      onProgressChange()
      showToast(
        action === 'solved_pyq' ? 'Nice — marked as solved' : `Marked "${current.topic_name}" as weak`,
        action === 'solved_pyq' ? 'success' : 'info',
      )
      setIndex((i) => i + 1)
    } catch {
      showToast('Could not update progress. Try again.', 'error')
    } finally {
      setMarking(false)
    }
  }

  if (!queue) {
    return (
      <div className="card-elevated flex flex-col items-center rounded-2xl border border-border bg-surface/40 p-10 text-center">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-border-strong bg-surface">
          <PenLine size={20} className="text-accent-2" />
        </div>
        <p className="mb-4 max-w-xs text-sm text-text-muted">
          Start a guided flow to answer repeated questions one by one.
        </p>
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={start}
          disabled={starting}
          className="flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-accent/15 transition-colors hover:bg-accent-hover disabled:opacity-60"
        >
          {starting && <Loader2 size={14} className="animate-spin" />}
          {starting ? 'Loading...' : 'Start Solving Repeated PYQs'}
        </motion.button>
      </div>
    )
  }

  if (!current) {
    return (
      <div className="card-elevated flex flex-col items-center rounded-2xl border border-border bg-surface/40 p-10 text-center">
        <CheckCircle2 size={28} className="mb-3 text-success" />
        <p className="mb-4 text-sm text-success">You completed all repeated-question practice items.</p>
        <button
          onClick={() => setIndex(0)}
          className="flex items-center gap-1.5 rounded-lg border border-border px-5 py-2.5 text-sm font-medium text-text transition-colors hover:border-accent hover:text-accent"
        >
          <RotateCcw size={14} />
          Restart PYQ Queue
        </button>
      </div>
    )
  }

  return (
    <motion.div
      key={index}
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.25 }}
      className="card-elevated space-y-4 rounded-2xl border border-border bg-surface/40 p-6"
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-border-strong bg-surface text-accent-2">
          <PenLine size={16} />
        </div>
        <div>
          <h3 className="font-display text-lg font-bold text-text">PYQ Practice</h3>
          <p className="tabular-nums mt-1 text-xs text-text-muted">
            Module {current.module_no} &middot; Year: {current.year} &middot; Marks: {current.marks} &middot;
            Topic: {current.topic_name ?? 'Unknown'}
          </p>
        </div>
      </div>

      <div>
        <p className="mb-1 text-sm font-semibold text-text">Question</p>
        <p className="text-sm text-text-muted">{current.question_text}</p>
      </div>

      <div>
        <p className="mb-1 text-sm font-semibold text-text">Exam-Style Answer</p>
        {loadingAnswer || answer === null ? (
          <div className="h-24 animate-pulse rounded-lg bg-surface" />
        ) : (
          <div className="text-text-muted">
            <Markdown>{answer}</Markdown>
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2 pt-2">
        {current.topic_name && (
          <>
            <button
              disabled={marking}
              onClick={() => mark('solved_pyq')}
              className="flex items-center gap-1.5 rounded-lg bg-success/15 px-4 py-2 text-sm font-medium text-success transition-colors hover:bg-success/25 disabled:opacity-50"
            >
              <CheckCircle2 size={13} />
              Solved
            </button>
            <button
              disabled={marking}
              onClick={() => mark('weak')}
              className="flex items-center gap-1.5 rounded-lg bg-accent/15 px-4 py-2 text-sm font-medium text-accent transition-colors hover:bg-accent/25 disabled:opacity-50"
            >
              <AlertTriangle size={13} />
              Weak
            </button>
          </>
        )}
        <button
          disabled={marking}
          onClick={() => setIndex((i) => i + 1)}
          className="flex items-center gap-1.5 rounded-lg border border-border px-4 py-2 text-sm font-medium text-text transition-colors hover:border-accent-2 hover:text-accent-2 disabled:opacity-50"
        >
          Next Question
          <ArrowRight size={13} />
        </button>
      </div>
    </motion.div>
  )
}
