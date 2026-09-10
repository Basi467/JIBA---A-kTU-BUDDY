import { motion } from 'framer-motion'
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  GraduationCap,
  Lightbulb,
  Loader2,
  RotateCcw,
  Sparkles,
} from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import { examApi, progressApi } from '../../api/endpoints'
import { useToast } from '../../context/ToastContext'
import Markdown, { MarkdownInline } from '../Markdown'
import type { TeachLesson, TeachTopicItem } from '../../types'

export default function TeachHighPriority({
  subject,
  onProgressChange,
}: {
  subject: string
  onProgressChange: () => void
}) {
  const [queue, setQueue] = useState<TeachTopicItem[] | null>(null)
  const [index, setIndex] = useState(0)
  const [lesson, setLesson] = useState<TeachLesson | null>(null)
  const [loadingLesson, setLoadingLesson] = useState(false)
  const [starting, setStarting] = useState(false)
  const [marking, setMarking] = useState(false)
  const { showToast } = useToast()

  useEffect(() => {
    setQueue(null)
    setIndex(0)
    setLesson(null)
  }, [subject])

  const current = queue && index < queue.length ? queue[index] : null

  useEffect(() => {
    if (!current) return
    setLoadingLesson(true)
    setLesson(null)
    examApi
      .teachTopic(subject, current.topic_name)
      .then(setLesson)
      .finally(() => setLoadingLesson(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current?.topic_name, index])

  async function start() {
    setStarting(true)
    try {
      const items = await examApi.teachQueue(subject)
      setQueue(items)
      setIndex(0)
    } finally {
      setStarting(false)
    }
  }

  async function mark(action: 'weak' | 'completed') {
    if (!current) return
    setMarking(true)
    try {
      await progressApi.mark(subject, current.topic_name, action)
      onProgressChange()
      showToast(
        action === 'completed' ? `"${current.topic_name}" marked done` : `"${current.topic_name}" marked weak`,
        action === 'completed' ? 'success' : 'info',
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
          <GraduationCap size={20} className="text-accent-2" />
        </div>
        <p className="mb-4 max-w-xs text-sm text-text-muted">
          Start a guided flow to learn one high-priority topic at a time.
        </p>
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={start}
          disabled={starting}
          className="flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-accent/15 transition-colors hover:bg-accent-hover disabled:opacity-60"
        >
          {starting && <Loader2 size={14} className="animate-spin" />}
          {starting ? 'Loading...' : 'Start Teaching High Priority Topics'}
        </motion.button>
      </div>
    )
  }

  if (!current) {
    return (
      <div className="card-elevated flex flex-col items-center rounded-2xl border border-border bg-surface/40 p-10 text-center">
        <CheckCircle2 size={28} className="mb-3 text-success" />
        <p className="mb-4 text-sm text-success">You completed all high-priority topics.</p>
        <button
          onClick={() => setIndex(0)}
          className="flex items-center gap-1.5 rounded-lg border border-border px-5 py-2.5 text-sm font-medium text-text transition-colors hover:border-accent hover:text-accent"
        >
          <RotateCcw size={14} />
          Restart Teaching Queue
        </button>
      </div>
    )
  }

  return (
    <motion.div
      key={current.topic_name}
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.25 }}
      className="card-elevated space-y-4 rounded-2xl border border-border bg-surface/40 p-6"
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-border-strong bg-surface text-accent-2">
          <BookOpen size={16} />
        </div>
        <div>
          <h3 className="font-display text-xl font-bold text-text">{current.topic_name}</h3>
          <p className="mt-1 text-xs text-text-muted">
            Module {current.module_no} &middot; Priority: {current.priority_label} &middot; Repeated:{' '}
            {current.question_count ?? 0}
          </p>
        </div>
      </div>

      {loadingLesson || !lesson ? (
        <div className="h-40 animate-pulse rounded-xl bg-surface" />
      ) : (
        <div className="space-y-4">
          <Section title="Simple Explanation" text={lesson.simple_explanation} />
          <Section title="Exam-Ready Answer" text={lesson.exam_answer} />

          {lesson.key_points.length > 0 && (
            <div>
              <p className="mb-1.5 text-sm font-semibold text-text">Key Points</p>
              <ul className="list-disc space-y-1 pl-5">
                {lesson.key_points.map((p, i) => (
                  <li key={i} className="text-sm text-text-muted">
                    <MarkdownInline>{p}</MarkdownInline>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {lesson.memory_tip && (
            <div className="flex items-start gap-2.5 rounded-lg border border-accent-2/30 bg-accent-2/10 p-3">
              <Lightbulb size={14} className="mt-0.5 shrink-0 text-accent-2" />
              <div>
                <p className="text-xs font-semibold text-accent-2">Memory Tip</p>
                <p className="text-sm text-text">
                  <MarkdownInline>{lesson.memory_tip}</MarkdownInline>
                </p>
              </div>
            </div>
          )}

          {lesson.related_pyqs.length > 0 && (
            <div>
              <p className="mb-1.5 text-sm font-semibold text-text">Related PYQs</p>
              <ul className="space-y-1">
                {lesson.related_pyqs.map((q, i) => (
                  <li key={i} className="tabular-nums text-xs text-text-muted">
                    [{q.year}] ({q.marks} marks) {q.question_text}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {lesson.practice_question && <Section title="Practice Question" text={lesson.practice_question} />}
        </div>
      )}

      <div className="flex flex-wrap gap-2 pt-2">
        <ActionButton disabled={marking} onClick={() => mark('weak')} tone="accent" icon={AlertTriangle}>
          Weak
        </ActionButton>
        <ActionButton disabled={marking} onClick={() => mark('completed')} tone="success" icon={CheckCircle2}>
          Done
        </ActionButton>
        <ActionButton disabled={marking} onClick={() => setIndex((i) => i + 1)} tone="neutral" icon={ArrowRight}>
          Next Topic
        </ActionButton>
        <ActionButton disabled={marking} onClick={() => setIndex(0)} tone="neutral" icon={RotateCcw}>
          Restart
        </ActionButton>
      </div>
    </motion.div>
  )
}

function Section({ title, text }: { title: string; text: string }) {
  if (!text) return null
  return (
    <div>
      <p className="mb-1 flex items-center gap-1.5 text-sm font-semibold text-text">
        <Sparkles size={12} className="text-accent-2" />
        {title}
      </p>
      <div className="text-text-muted">
        <Markdown>{text}</Markdown>
      </div>
    </div>
  )
}

function ActionButton({
  children,
  onClick,
  disabled,
  tone,
  icon: Icon,
}: {
  children: ReactNode
  onClick: () => void
  disabled: boolean
  tone: 'accent' | 'success' | 'neutral'
  icon: typeof AlertTriangle
}) {
  const toneClass =
    tone === 'accent'
      ? 'bg-accent/15 text-accent hover:bg-accent/25'
      : tone === 'success'
        ? 'bg-success/15 text-success hover:bg-success/25'
        : 'border border-border text-text hover:border-accent-2 hover:text-accent-2'

  return (
    <motion.button
      whileTap={{ scale: 0.96 }}
      onClick={onClick}
      disabled={disabled}
      className={`flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 ${toneClass}`}
    >
      <Icon size={13} />
      {children}
    </motion.button>
  )
}
