import { AnimatePresence, motion } from 'framer-motion'
import { Loader2, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { subjectsApi } from '../api/endpoints'
import ExamMode from '../components/exam/ExamMode'
import InsightsPanel from '../components/InsightsPanel'
import TopBar from '../components/TopBar'
import TutorChat from '../components/TutorChat'
import type { Subject } from '../types'

export default function DashboardPage() {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [selectedSubject, setSelectedSubject] = useState('')
  const [examMode, setExamMode] = useState(false)
  const [hoursPerDay, setHoursPerDay] = useState(3)
  const [refreshKey, setRefreshKey] = useState(0)
  const [insightsOpen, setInsightsOpen] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    subjectsApi
      .list()
      .then((list) => {
        setSubjects(list)
        if (list.length > 0) setSelectedSubject(list[0].subject_name)
      })
      .finally(() => setLoading(false))
  }, [])

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
        onOpenInsights={() => setInsightsOpen(true)}
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
                <ExamMode
                  subject={selectedSubject}
                  hoursPerDay={hoursPerDay}
                  onProgressChange={() => setRefreshKey((k) => k + 1)}
                />
              ) : (
                <TutorChat subject={selectedSubject} hoursPerDay={hoursPerDay} />
              )}
            </motion.div>
          </div>
        </main>

        <aside className="hidden w-80 shrink-0 overflow-y-auto border-l border-border p-5 xl:block">
          <InsightsPanel subject={selectedSubject} refreshKey={refreshKey} />
        </aside>
      </div>

      <AnimatePresence>
        {insightsOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setInsightsOpen(false)}
              className="fixed inset-0 z-40 bg-black/60 xl:hidden"
            />
            <motion.aside
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', stiffness: 320, damping: 34 }}
              className="fixed inset-y-0 right-0 z-50 w-full max-w-sm overflow-y-auto border-l border-border bg-bg p-5 xl:hidden"
            >
              <button
                onClick={() => setInsightsOpen(false)}
                className="mb-4 flex h-8 w-8 items-center justify-center rounded-full border border-border text-text-muted transition-colors hover:border-accent hover:text-accent"
              >
                <X size={15} />
              </button>
              <InsightsPanel subject={selectedSubject} refreshKey={refreshKey} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
