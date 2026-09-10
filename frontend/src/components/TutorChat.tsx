import { useQuery } from '@tanstack/react-query'
import { AnimatePresence, motion } from 'framer-motion'
import { Bot, CalendarDays, SendHorizontal, Sparkles } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { chatApi, progressApi, studyPlanApi } from '../api/endpoints'
import Markdown from './Markdown'
import StudyPlanList from './StudyPlanList'
import type { ChatMessage, StudyPlanItem } from '../types'

const STUDY_PLAN_KEYWORDS = [
  'study plan',
  'revision plan',
  'make a plan',
  'create a plan',
  'schedule',
  'timetable',
  'how should i study',
  'plan for exam',
  'days left',
  'exam in',
]

const SUGGESTED_PROMPTS = [
  'What are the most important topics?',
  'Explain module 1 in simple terms',
  'Make me a 5-day study plan',
  'Quiz me on a random topic',
]

function detectStudyPlanIntent(text: string): boolean {
  const lower = text.toLowerCase()
  return STUDY_PLAN_KEYWORDS.some((k) => lower.includes(k))
}

function extractDays(text: string): number | null {
  const lower = text.toLowerCase()
  const m1 = lower.match(/(\d+)\s+days?/)
  if (m1) return Number(m1[1])
  const m2 = lower.match(/exam\s+in\s+(\d+)/)
  if (m2) return Number(m2[1])
  return null
}

function StudyPlanCard({ plan }: { plan: StudyPlanItem[] }) {
  return (
    <div>
      <p className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-text">
        <CalendarDays size={14} className="text-accent-2" />
        Study Plan
      </p>
      <StudyPlanList plan={plan} />
    </div>
  )
}

function EmptyState({ subject, onPick }: { subject: string; onPick: (prompt: string) => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-border-strong bg-surface">
        <Sparkles size={22} className="text-accent-2" />
      </div>
      <h3 className="font-display text-lg font-semibold text-text">Ask your tutor anything</h3>
      <p className="mt-1.5 max-w-sm text-sm text-text-muted">
        Answers stay grounded in the <span className="text-text">{subject}</span> syllabus and past-year
        question patterns.
      </p>
      <div className="mt-6 grid w-full max-w-md grid-cols-1 gap-2 sm:grid-cols-2">
        {SUGGESTED_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            onClick={() => onPick(prompt)}
            className="rounded-xl border border-border bg-surface px-3.5 py-2.5 text-left text-xs text-text-muted transition-colors hover:border-accent-2/50 hover:text-text"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  )
}

interface DisplayMessage extends ChatMessage {
  studyPlan?: StudyPlanItem[]
}

export default function TutorChat({ subject, hoursPerDay }: { subject: string; hoursPerDay: number }) {
  const { data: history, isFetched: historyLoaded } = useQuery({
    queryKey: ['chat', 'history', subject],
    queryFn: () => chatApi.history(subject),
    enabled: !!subject,
    // Local `messages` below is the live source of truth once loaded (it
    // also carries locally-synthesized study-plan cards /chat/history never
    // returns) — a background refetch overwriting it mid-conversation would
    // silently drop those, so this query is deliberately fetch-once.
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  })

  // Local state, not the query cache directly: locally-appended messages
  // carry a `studyPlan` card that /chat/history never returns, and are
  // appended optimistically before the server round-trip completes.
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setMessages(history ?? [])
  }, [subject, history])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  async function handleSubmit(overrideText?: string) {
    const question = (overrideText ?? input).trim()
    if (!question || sending) return

    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setSending(true)

    try {
      if (detectStudyPlanIntent(question)) {
        const days = extractDays(question) ?? 7
        const examDate = new Date()
        examDate.setDate(examDate.getDate() + days)

        const weak = await progressApi.get(subject).then((p) => p.weak)
        const plan = await studyPlanApi.generate(
          subject,
          examDate.toISOString().slice(0, 10),
          hoursPerDay,
          weak,
        )
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `Here's a study plan for the next ${days} days.`, studyPlan: plan },
        ])
      } else {
        const reply = await chatApi.ask(subject, question)
        setMessages((prev) => [...prev, { role: 'assistant', content: reply }])
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Something went wrong generating a response. Please try again.' },
      ])
    } finally {
      setSending(false)
    }
  }

  const showEmptyState = historyLoaded && messages.length === 0 && !sending

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-1 pb-4">
        {!historyLoaded && <div className="h-24 animate-pulse rounded-xl bg-surface" />}

        {showEmptyState && <EmptyState subject={subject} onPick={(p) => handleSubmit(p)} />}

        <div className="space-y-4">
          <AnimatePresence initial={false}>
            {messages.map((msg, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
                className={`flex items-end gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role !== 'user' && (
                  <div className="mb-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-border-strong bg-surface-2 text-accent-2">
                    <Bot size={13} />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-accent text-white'
                      : 'card-elevated border border-border bg-surface text-text'
                  }`}
                >
                  {msg.studyPlan ? (
                    <StudyPlanCard plan={msg.studyPlan} />
                  ) : msg.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <Markdown>{msg.content}</Markdown>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {sending && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-end gap-2">
              <div className="mb-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-border-strong bg-surface-2 text-accent-2">
                <Bot size={13} />
              </div>
              <div className="flex items-center gap-1.5 rounded-2xl border border-border bg-surface px-4 py-3">
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    animate={{ y: [0, -4, 0] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }}
                    className="h-1.5 w-1.5 rounded-full bg-text-muted"
                  />
                ))}
              </div>
            </motion.div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      <div className="flex gap-2 border-t border-border pt-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          placeholder={`Ask anything from ${subject}`}
          className="flex-1 rounded-xl border border-border bg-surface px-4 py-2.5 text-sm text-text placeholder:text-text-faint focus:border-accent-2 focus:outline-none focus:ring-1 focus:ring-accent-2"
        />
        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={() => handleSubmit()}
          disabled={sending || !input.trim()}
          className="flex items-center gap-1.5 rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-accent/15 transition-colors hover:bg-accent-hover disabled:opacity-50 disabled:shadow-none"
        >
          <SendHorizontal size={15} />
          <span className="hidden sm:inline">Send</span>
        </motion.button>
      </div>
    </div>
  )
}
