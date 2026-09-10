import { motion } from 'framer-motion'
import { ArrowLeft, Loader2, MailCheck } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiErrorMessage } from '../api/client'
import { authApi } from '../api/endpoints'

const inputClass =
  'w-full rounded-xl border border-border bg-surface px-3.5 py-2.5 text-sm text-text placeholder:text-text-faint focus:border-accent-2 focus:outline-none focus:ring-1 focus:ring-accent-2 transition-colors'

const labelClass = 'mb-1.5 block text-xs font-medium text-text-muted'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const msg = await authApi.forgotPassword(email)
      setMessage(msg)
    } catch (err) {
      setError(apiErrorMessage(err, 'Something went wrong. Try again.'))
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

        <h2 className="font-display text-2xl font-bold text-text">Reset your password</h2>
        <p className="mt-1.5 text-sm text-text-muted">
          Enter the email on your account and we'll send you a reset link.
        </p>

        {message ? (
          <div className="mt-6 flex items-start gap-3 rounded-xl border border-success/25 bg-success/10 px-4 py-3.5">
            <MailCheck size={18} className="mt-0.5 shrink-0 text-success" />
            <p className="text-sm text-text">{message}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label htmlFor="forgot-email" className={labelClass}>
                Email
              </label>
              <input
                id="forgot-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={inputClass}
                placeholder="you@example.com"
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
              {submitting ? 'Sending...' : 'Send reset link'}
            </motion.button>
          </form>
        )}

        <Link
          to="/login"
          className="mt-6 flex items-center gap-1.5 text-sm text-text-muted transition-colors hover:text-text"
        >
          <ArrowLeft size={14} />
          Back to login
        </Link>
      </motion.div>
    </div>
  )
}
