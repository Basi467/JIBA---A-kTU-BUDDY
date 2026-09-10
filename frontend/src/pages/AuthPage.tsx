import { motion } from 'framer-motion'
import { GraduationCap, Loader2, MessageSquareText, Sparkles, Target } from 'lucide-react'
import { type FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi, metaApi } from '../api/endpoints'
import { apiErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import type { SchemeOptions } from '../types'

type Tab = 'login' | 'register'

const FEATURES = [
  {
    icon: MessageSquareText,
    title: 'AI tutor, grounded in your syllabus',
    body: 'Ask anything — answers stay scoped to your modules and past-year patterns.',
  },
  {
    icon: Target,
    title: 'Know what actually gets asked',
    body: 'Topics ranked by real exam frequency, not guesswork.',
  },
  {
    icon: Sparkles,
    title: 'A study plan that adapts to you',
    body: 'Built from your weak topics and the days you have left.',
  },
]

export default function AuthPage() {
  const [tab, setTab] = useState<Tab>('login')

  return (
    <div className="flex min-h-screen bg-bg">
      <div className="relative hidden w-[44%] shrink-0 overflow-hidden border-r border-border bg-surface/40 lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              'radial-gradient(700px circle at 20% 10%, rgba(79,140,255,0.16), transparent 55%), radial-gradient(600px circle at 90% 90%, rgba(239,68,68,0.14), transparent 55%)',
          }}
        />

        <div className="relative flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-accent-2 to-accent text-lg font-bold text-white shadow-lg shadow-accent/25">
            J
          </div>
          <span className="font-display text-xl font-bold text-text">JIBA</span>
        </div>

        <div className="relative">
          <h1 className="font-display max-w-sm text-4xl font-bold leading-tight text-text">
            Your KTU exam prep, actually organized.
          </h1>
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-text-muted">
            Syllabus, previous-year questions, and an AI tutor — all in one place, scoped to your
            department and semester.
          </p>

          <div className="mt-10 space-y-5">
            {FEATURES.map((f) => (
              <div key={f.title} className="flex items-start gap-3.5">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-border-strong bg-surface-2 text-accent-2">
                  <f.icon size={16} strokeWidth={2} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-text">{f.title}</p>
                  <p className="mt-0.5 text-xs leading-relaxed text-text-muted">{f.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="relative flex items-center gap-2 text-xs text-text-faint">
          <GraduationCap size={14} />
          Built for KTU students, by a KTU student.
        </div>
      </div>

      <div className="flex flex-1 items-center justify-center px-4 py-10 sm:px-6">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: 'easeOut' }}
          className="w-full max-w-sm"
        >
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-accent-2 to-accent text-lg font-bold text-white shadow-lg shadow-accent/20">
              J
            </div>
            <div>
              <h1 className="font-display text-xl font-bold text-text">JIBA</h1>
              <p className="text-xs text-text-muted">AI study assistant for KTU students</p>
            </div>
          </div>

          <h2 className="font-display text-2xl font-bold text-text">
            {tab === 'login' ? 'Welcome back' : 'Create your account'}
          </h2>
          <p className="mt-1.5 text-sm text-text-muted">
            {tab === 'login'
              ? 'Log in to continue your study session.'
              : 'Set up your profile to unlock your subjects.'}
          </p>

          <div className="mb-6 mt-6 flex gap-1 rounded-xl border border-border bg-surface p-1">
            {(['login', 'register'] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className="relative flex-1 rounded-lg py-2 text-sm font-medium capitalize transition-colors"
              >
                {tab === t && (
                  <motion.div layoutId="auth-tab-bg" className="absolute inset-0 rounded-lg bg-accent" />
                )}
                <span className={`relative ${tab === t ? 'text-white' : 'text-text-muted hover:text-text'}`}>
                  {t}
                </span>
              </button>
            ))}
          </div>

          {tab === 'login' ? <LoginForm /> : <RegisterForm onRegistered={() => setTab('login')} />}
        </motion.div>
      </div>
    </div>
  )
}

const inputClass =
  'w-full rounded-xl border border-border bg-surface px-3.5 py-2.5 text-sm text-text placeholder:text-text-faint focus:border-accent-2 focus:outline-none focus:ring-1 focus:ring-accent-2 transition-colors'

const labelClass = 'mb-1.5 block text-xs font-medium text-text-muted'

function SubmitButton({ submitting, children }: { submitting: boolean; children: string }) {
  return (
    <motion.button
      whileTap={{ scale: 0.98 }}
      type="submit"
      disabled={submitting}
      className="flex w-full items-center justify-center gap-2 rounded-xl bg-accent py-2.5 text-sm font-semibold text-white shadow-lg shadow-accent/20 transition-colors hover:bg-accent-hover disabled:opacity-60"
    >
      {submitting && <Loader2 size={15} className="animate-spin" />}
      {children}
    </motion.button>
  )
}

function LoginForm() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(apiErrorMessage(err, 'Invalid email or password.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="login-email" className={labelClass}>
          Email
        </label>
        <input
          id="login-email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={inputClass}
          placeholder="you@example.com"
        />
      </div>
      <div>
        <div className="flex items-center justify-between">
          <label htmlFor="login-password" className={labelClass}>
            Password
          </label>
          <Link to="/forgot-password" className="mb-1.5 text-xs font-medium text-accent-2 hover:text-accent">
            Forgot password?
          </Link>
        </div>
        <input
          id="login-password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={inputClass}
          placeholder="Enter your password"
        />
      </div>

      {error && (
        <p className="rounded-lg border border-accent/25 bg-accent/10 px-3 py-2 text-sm text-accent">
          {error}
        </p>
      )}

      <SubmitButton submitting={submitting}>{submitting ? 'Logging in...' : 'Login'}</SubmitButton>
    </form>
  )
}

function RegisterForm({ onRegistered }: { onRegistered: () => void }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const [options, setOptions] = useState<SchemeOptions[] | null>(null)
  const [optionsError, setOptionsError] = useState(false)
  const [scheme, setScheme] = useState('')
  const [department, setDepartment] = useState('')
  const [semester, setSemester] = useState<number | ''>('')

  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    metaApi
      .signupOptions()
      .then((opts) => {
        setOptions(opts)
        const firstScheme = opts[0]
        const firstDept = firstScheme?.departments[0]
        setScheme(firstScheme?.scheme ?? '')
        setDepartment(firstDept?.department ?? '')
        setSemester(firstDept?.semesters[0] ?? '')
      })
      .catch(() => setOptionsError(true))
  }, [])

  const schemeOptions = options ?? []
  const departmentOptions = schemeOptions.find((o) => o.scheme === scheme)?.departments ?? []
  const semesterOptions = departmentOptions.find((d) => d.department === department)?.semesters ?? []

  function handleSchemeChange(nextScheme: string) {
    setScheme(nextScheme)
    const depts = schemeOptions.find((o) => o.scheme === nextScheme)?.departments ?? []
    setDepartment(depts[0]?.department ?? '')
    setSemester(depts[0]?.semesters[0] ?? '')
  }

  function handleDepartmentChange(nextDepartment: string) {
    setDepartment(nextDepartment)
    const semesters = departmentOptions.find((d) => d.department === nextDepartment)?.semesters ?? []
    setSemester(semesters[0] ?? '')
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    if (password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (!scheme || !department || !semester) {
      setError('Please select a scheme, department, and semester.')
      return
    }

    setSubmitting(true)
    try {
      await authApi.register({ name, email, password, scheme, department, semester })
      setSuccess('Account created. Redirecting to login...')
      setTimeout(onRegistered, 900)
    } catch (err) {
      setError(apiErrorMessage(err, 'Registration failed.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className={labelClass}>Full Name</label>
        <input
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          className={inputClass}
          placeholder="Enter your name"
        />
      </div>
      <div>
        <label className={labelClass}>Email</label>
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={inputClass}
          placeholder="you@example.com"
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className={labelClass}>Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputClass}
            placeholder="Min. 6 chars"
          />
        </div>
        <div>
          <label className={labelClass}>Confirm</label>
          <input
            type="password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className={inputClass}
            placeholder="Re-enter"
          />
        </div>
      </div>

      <div className="border-t border-border pt-4">
        <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-text-muted">
          Academic Profile
        </p>

        {optionsError ? (
          <p className="rounded-lg border border-accent/25 bg-accent/10 px-3 py-2 text-sm text-accent">
            Couldn't load available departments. Refresh and try again.
          </p>
        ) : options === null ? (
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <Loader2 size={14} className="animate-spin" />
            Loading available subjects...
          </div>
        ) : (
          <>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className={labelClass}>Scheme</label>
                <select
                  value={scheme}
                  onChange={(e) => handleSchemeChange(e.target.value)}
                  className={inputClass}
                >
                  {schemeOptions.map((o) => (
                    <option key={o.scheme} value={o.scheme}>
                      {o.scheme}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className={labelClass}>Dept.</label>
                <select
                  value={department}
                  onChange={(e) => handleDepartmentChange(e.target.value)}
                  className={inputClass}
                >
                  {departmentOptions.map((d) => (
                    <option key={d.department} value={d.department}>
                      {d.department}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className={labelClass}>Sem.</label>
                <select
                  value={semester}
                  onChange={(e) => setSemester(Number(e.target.value))}
                  className={inputClass}
                >
                  {semesterOptions.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <p className="mt-2 text-[11px] text-text-faint">
              Only showing departments/semesters with a fully-prepared syllabus and exam question
              bank.
            </p>
          </>
        )}
      </div>

      {error && (
        <p className="rounded-lg border border-accent/25 bg-accent/10 px-3 py-2 text-sm text-accent">
          {error}
        </p>
      )}
      {success && (
        <p className="rounded-lg border border-success/25 bg-success/10 px-3 py-2 text-sm text-success">
          {success}
        </p>
      )}

      <SubmitButton submitting={submitting}>{submitting ? 'Creating account...' : 'Create Account'}</SubmitButton>
    </form>
  )
}
