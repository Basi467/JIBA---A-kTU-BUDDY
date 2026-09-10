import { AlertTriangle, RotateCcw } from 'lucide-react'
import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // In a real deployment this is where you'd forward to an error-tracking
    // service (Sentry, etc.) — for now, at least don't lose it silently.
    console.error('Unhandled render error:', error, info.componentStack)
  }

  handleReload = () => {
    this.setState({ hasError: false })
    window.location.href = '/'
  }

  render() {
    if (!this.state.hasError) return this.props.children

    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-bg px-6 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-accent/30 bg-accent/10 text-accent">
          <AlertTriangle size={22} />
        </div>
        <div>
          <h1 className="font-display text-lg font-bold text-text">Something went wrong</h1>
          <p className="mt-1.5 max-w-sm text-sm text-text-muted">
            An unexpected error occurred. Try reloading — if it keeps happening, let us know what
            you were doing.
          </p>
        </div>
        <button
          onClick={this.handleReload}
          className="flex items-center gap-2 rounded-xl bg-accent px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-accent/20 transition-colors hover:bg-accent-hover"
        >
          <RotateCcw size={14} />
          Reload
        </button>
      </div>
    )
  }
}
