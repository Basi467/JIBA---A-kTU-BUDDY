import * as Popover from '@radix-ui/react-popover'
import { Check, ChevronDown, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { Subject } from '../types'

export default function SubjectSwitcher({
  subjects,
  selected,
  onSelect,
}: {
  subjects: Subject[]
  selected: string
  onSelect: (name: string) => void
}) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return subjects
    return subjects.filter((s) => s.subject_name.toLowerCase().includes(q))
  }, [subjects, query])

  return (
    <Popover.Root
      open={open}
      onOpenChange={(next) => {
        setOpen(next)
        if (!next) setQuery('')
      }}
    >
      <Popover.Trigger asChild>
        <button className="flex w-full min-w-0 max-w-xs items-center gap-2 rounded-full border border-border bg-surface px-4 py-2 text-sm font-medium text-text transition-colors hover:border-accent-2 sm:max-w-sm">
          <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent-2" />
          <span className="min-w-0 flex-1 truncate text-left">{selected || 'Select subject'}</span>
          <ChevronDown
            size={14}
            strokeWidth={2.25}
            className={`shrink-0 text-text-muted transition-transform ${open ? 'rotate-180' : ''}`}
          />
        </button>
      </Popover.Trigger>

      <Popover.Portal>
        <Popover.Content
          sideOffset={8}
          align="start"
          className="animate-pop-in z-50 w-80 overflow-hidden rounded-2xl border border-border bg-surface-2 shadow-2xl shadow-black/40"
        >
          <div className="flex items-center gap-2 border-b border-border px-3">
            <Search size={14} className="shrink-0 text-text-faint" />
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search subjects..."
              className="w-full bg-transparent py-2.5 text-sm text-text placeholder:text-text-faint focus:outline-none"
            />
          </div>
          <div className="max-h-80 overflow-y-auto p-1.5">
            {filtered.length === 0 && (
              <p className="px-3 py-4 text-center text-sm text-text-muted">No subjects match.</p>
            )}
            {filtered.map((s) => (
              <button
                key={s.subject_code}
                onClick={() => {
                  onSelect(s.subject_name)
                  setOpen(false)
                  setQuery('')
                }}
                className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                  s.subject_name === selected
                    ? 'bg-accent/15 text-accent'
                    : 'text-text hover:bg-surface'
                }`}
              >
                {s.subject_name === selected ? (
                  <Check size={14} className="shrink-0" />
                ) : (
                  <span className="w-3.5 shrink-0" />
                )}
                <span className="min-w-0 flex-1 truncate">{s.subject_name}</span>
                <span className="shrink-0 font-mono text-[11px] text-text-faint">{s.subject_code}</span>
              </button>
            ))}
          </div>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  )
}
