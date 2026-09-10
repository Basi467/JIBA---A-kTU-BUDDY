import * as Popover from '@radix-ui/react-popover'
import { BarChart3, Settings2 } from 'lucide-react'
import { motion } from 'framer-motion'
import ProfileMenu from './ProfileMenu'
import SubjectSwitcher from './SubjectSwitcher'
import type { Subject } from '../types'

interface TopBarProps {
  subjects: Subject[]
  selectedSubject: string
  onSelectSubject: (name: string) => void
  examMode: boolean
  onToggleExamMode: (value: boolean) => void
  hoursPerDay: number
  onChangeHoursPerDay: (value: number) => void
  onOpenInsights?: () => void
}

export default function TopBar({
  subjects,
  selectedSubject,
  onSelectSubject,
  examMode,
  onToggleExamMode,
  hoursPerDay,
  onChangeHoursPerDay,
  onOpenInsights,
}: TopBarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center gap-1.5 border-b border-border bg-bg/85 px-2.5 backdrop-blur-xl sm:gap-3 sm:px-6">
      <div className="flex shrink-0 items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-accent-2 to-accent text-sm font-bold text-white shadow-md shadow-accent/20">
          J
        </div>
        <span className="font-display hidden text-base font-bold text-text sm:inline">JIBA</span>
      </div>

      <div className="hidden h-6 w-px shrink-0 bg-border sm:block" />

      <div className="min-w-[84px] flex-1">
        <SubjectSwitcher subjects={subjects} selected={selectedSubject} onSelect={onSelectSubject} />
      </div>

      <button
        onClick={() => onToggleExamMode(!examMode)}
        role="switch"
        aria-checked={examMode}
        aria-label="Toggle exam mode"
        className={`flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-medium transition-colors ${
          examMode
            ? 'border-accent/40 bg-accent/15 text-accent'
            : 'border-border bg-surface text-text-muted hover:text-text'
        }`}
      >
        <span className="relative flex h-4 w-7 shrink-0 items-center rounded-full bg-white/10">
          <motion.span
            layout
            transition={{ type: 'spring', stiffness: 500, damping: 32 }}
            className={`absolute h-3 w-3 rounded-full ${examMode ? 'bg-accent' : 'bg-white/60'}`}
            style={{ left: examMode ? '14px' : '2px' }}
          />
        </span>
        <span className="hidden sm:inline">Exam Mode</span>
      </button>

      <Popover.Root>
        <Popover.Trigger asChild>
          <button
            title="Study settings"
            aria-label="Study settings"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border bg-surface text-text-muted transition-colors hover:border-accent-2 hover:text-accent-2"
          >
            <Settings2 size={16} strokeWidth={2} />
          </button>
        </Popover.Trigger>
        <Popover.Portal>
          <Popover.Content
            sideOffset={10}
            align="end"
            className="animate-pop-in z-50 w-64 rounded-2xl border border-border bg-surface-2 p-4 shadow-2xl shadow-black/40"
          >
            <p className="mb-3 text-sm font-semibold text-text">Study Settings</p>
            <label htmlFor="hours-per-day" className="mb-1.5 block text-xs text-text-muted">
              Hours per day
            </label>
            <input
              id="hours-per-day"
              type="range"
              min={1}
              max={12}
              step={0.5}
              value={hoursPerDay}
              onChange={(e) => onChangeHoursPerDay(Number(e.target.value))}
              className="w-full accent-accent"
            />
            <p className="tabular-nums mt-1 text-right text-xs text-text-muted">{hoursPerDay}h / day</p>
          </Popover.Content>
        </Popover.Portal>
      </Popover.Root>

      {onOpenInsights && (
        <button
          onClick={onOpenInsights}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border bg-surface text-text-muted transition-colors hover:border-accent-2 hover:text-accent-2 xl:hidden"
          title="Progress & insights"
          aria-label="Progress & insights"
        >
          <BarChart3 size={16} strokeWidth={2} />
        </button>
      )}

      <ProfileMenu />
    </header>
  )
}
