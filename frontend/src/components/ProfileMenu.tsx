import * as DropdownMenu from '@radix-ui/react-dropdown-menu'
import { LogOut } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function ProfileMenu() {
  const { user, logout } = useAuth()
  if (!user) return null

  const initial = user.name.trim().charAt(0).toUpperCase() || '?'

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-accent-2 to-accent text-sm font-bold text-white shadow-md shadow-accent/20 transition-transform hover:scale-105">
          {initial}
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          sideOffset={10}
          align="end"
          className="animate-pop-in z-50 w-64 overflow-hidden rounded-2xl border border-border bg-surface-2 p-1.5 shadow-2xl shadow-black/40"
        >
          <div className="px-3 py-2.5">
            <p className="text-sm font-semibold text-text">{user.name}</p>
            <p className="mt-0.5 text-xs text-text-muted">{user.email}</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              <span className="rounded-full bg-surface px-2 py-0.5 text-[11px] text-text-muted">
                {user.department}
              </span>
              <span className="rounded-full bg-surface px-2 py-0.5 text-[11px] text-text-muted">
                Sem {user.semester}
              </span>
              <span className="rounded-full bg-surface px-2 py-0.5 text-[11px] text-text-muted">
                {user.scheme}
              </span>
            </div>
          </div>

          <DropdownMenu.Separator className="my-1.5 h-px bg-border" />

          <DropdownMenu.Item
            onSelect={logout}
            className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm text-accent outline-none transition-colors hover:bg-accent/10 data-[highlighted]:bg-accent/10"
          >
            <LogOut size={14} />
            Logout
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  )
}
