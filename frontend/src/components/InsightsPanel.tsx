import PredictedTopicsPanel from './PredictedTopicsPanel'
import ProgressPanel from './ProgressPanel'

export default function InsightsPanel({ subject, refreshKey }: { subject: string; refreshKey: number }) {
  return (
    <div className="space-y-4">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted">Insights</h2>
      <ProgressPanel subject={subject} refreshKey={refreshKey} />
      <PredictedTopicsPanel subject={subject} />
    </div>
  )
}
