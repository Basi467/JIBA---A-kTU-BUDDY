import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Loader2, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { subjectsApi } from '../api/endpoints'
import ExamMode from '../components/exam/ExamMode'
import InsightsPanel from '../components/InsightsPanel'
import TopBar from '../components/TopBar'
import TutorChat from '../components/TutorChat'

export default function DashboardPage() {
  const { data: subjects = [], isLoading: loading } = useQuery({
    queryKey: ['subjects'],
    queryFn: subjectsApi.list,
  })
  const [selectedSubject, setSelectedSubject] = useState('')
  const [examMode, setExamMode] = useState(false)
  const [hoursPerDay, setHoursPerDay] = useState(3)
  const [insightsOpen, setInsightsOpen] = useState(false)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const previouslyFocusedRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (!selectedSubject && subjects.length > 0) {
      setSelectedSubject(subjects[0].subject_name)
    }
  }, [subjects, selectedSubject])

  function openInsights() {
    previouslyFocusedRef.current = document.activeElement as HTMLElement
    setInsightsOpen(true)
  }

  function closeInsights() {
    setInsightsOpen(false)
    previouslyFocusedRef.current?.focus()
  }

  useEffect(() => {
    if (!insightsOpen) return
    closeButtonRef.current?.focus()
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') closeInsights()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [insightsOpen])

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center gap-2 bg-bg text-text-muted">
        <Loader2 size={16} className="animate-spin" />
        Loading...
      </div>
    )
  }

  if (subjects.length === 0) {
    return (
      <div className="flex h-screen items-center justify-center bg-bg text-text-muted">
        No subjects found for your profile.
      </div>
    )
  }

  return (
    <div className="flex h-screen flex-col bg-bg">
      <TopBar
        subjects={subjects}
        selectedSubject={selectedSubject}
        onSelectSubject={setSelectedSubject}
        examMode={examMode}
        onToggleExamMode={setExamMode}
        hoursPerDay={hoursPerDay}
        onChangeHoursPerDay={setHoursPerDay}
        onOpenInsights={openInsights}
      />

      <div className="flex min-h-0 flex-1">
        <main className="min-w-0 flex-1 overflow-y-auto">
          <div className="mx-auto h-full max-w-4xl px-4 py-6 sm:px-6">
            <motion.div
              key={`${selectedSubject}-${examMode}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              {examMode ? (
                <ExamMode subject={selectedSubject} hoursPerDay={hoursPerDay} />
              ) : (
                <TutorChat subject={selectedSubject} hoursPerDay={hoursPerDay} />
              )}
            </motion.div>
          </div>
        </main>

        <aside className="hidden w-80 shrink-0 overflow-y-auto border-l border-border p-5 xl:block">
          <InsightsPanel subject={selectedSubject} />
        </aside>
      </div>

      {insightsOpen && (
        <>
          <div onClick={closeInsights} className="fixed inset-0 z-40 bg-black/60 xl:hidden" />
          <motion.aside
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            transition={{ type: 'spring', stiffness: 320, damping: 34 }}
            role="dialog"
            aria-modal="true"
            aria-label="Insights"
            className="fixed inset-y-0 right-0 z-50 w-full max-w-sm overflow-y-auto border-l border-border bg-bg p-5 xl:hidden"
          >
            <button
              ref={closeButtonRef}
              onClick={closeInsights}
              aria-label="Close insights"
              className="mb-4 flex h-8 w-8 items-center justify-center rounded-full border border-border text-text-muted transition-colors hover:border-accent hover:text-accent"
            >
              <X size={15} />
            </button>
            <InsightsPanel subject={selectedSubject} />
          </motion.aside>
        </>
      )}
    </div>
  )
}
