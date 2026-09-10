import { motion } from 'framer-motion'
import { CheckCircle2, Loader2 } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { apiErrorMessage } from '../api/client'
import { authApi } from '../api/endpoints'

const inputClass =
  'w-full rounded-xl border border-border bg-surface px-3.5 py-2.5 text-sm text-text placeholder:text-text-faint focus:border-accent-2 focus:outline-none focus:ring-1 focus:ring-accent-2 transition-colors'

const labelClass = 'mb-1.5 block text-xs font-medium text-text-muted'

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setSubmitting(true)
    try {
      await authApi.resetPassword(token, newPassword)
      setDone(true)
    } catch (err) {
      setError(apiErrorMessage(err, 'This reset link is invalid or has expired.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-4 py-10 sm:px-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="w-full max-w-sm"
      >
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-accent-2 to-accent text-lg font-bold text-white shadow-lg shadow-accent/20">
            J
          </div>
          <div>
            <h1 className="font-display text-xl font-bold text-text">JIBA</h1>
            <p className="text-xs text-text-muted">AI study assistant for KTU students</p>
          </div>
        </div>

        {!token ? (
          <p className="rounded-lg border border-accent/25 bg-accent/10 px-3 py-2 text-sm text-accent">
            This reset link is missing its token. Request a new one from the login page.
          </p>
        ) : done ? (
          <div className="flex items-start gap-3 rounded-xl border border-success/25 bg-success/10 px-4 py-3.5">
            <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-success" />
            <p className="text-sm text-text">Password updated. You can now log in.</p>
          </div>
        ) : (
          <>
            <h2 className="font-display text-2xl font-bold text-text">Choose a new password</h2>
            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <div>
                <label htmlFor="reset-new-password" className={labelClass}>
                  New password
                </label>
                <input
                  id="reset-new-password"
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className={inputClass}
                  placeholder="Min. 6 chars"
                />
              </div>
              <div>
                <label htmlFor="reset-confirm-password" className={labelClass}>
                  Confirm password
                </label>
                <input
                  id="reset-confirm-password"
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className={inputClass}
                  placeholder="Re-enter"
                />
              </div>

              {error && (
                <p className="rounded-lg border border-accent/25 bg-accent/10 px-3 py-2 text-sm text-accent">
                  {error}
                </p>
              )}

              <motion.button
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={submitting}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-accent py-2.5 text-sm font-semibold text-white shadow-lg shadow-accent/20 transition-colors hover:bg-accent-hover disabled:opacity-60"
              >
                {submitting && <Loader2 size={15} className="animate-spin" />}
                {submitting ? 'Updating...' : 'Update password'}
              </motion.button>
            </form>
          </>
        )}

        <Link
          to="/login"
          className="mt-6 block text-sm text-text-muted transition-colors hover:text-text"
        >
          Back to login
        </Link>
      </motion.div>
    </div>
  )
}
