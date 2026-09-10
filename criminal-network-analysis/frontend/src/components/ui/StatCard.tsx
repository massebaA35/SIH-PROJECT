import type { LucideIcon } from 'lucide-react'

export default function StatCard({
  label, value, delta, icon: Icon, tone = 'accent',
}: {
  label: string
  value: string | number
  delta?: string
  icon: LucideIcon
  tone?: 'accent' | 'accent2' | 'info' | 'danger'
}) {
  const toneClasses: Record<string, string> = {
    accent: 'bg-accent/15 text-accent',
    accent2: 'bg-accent2/15 text-accent2',
    info: 'bg-info/15 text-info',
    danger: 'bg-danger/15 text-danger',
  }
  return (
    <div className="panel p-4">
      <div className="flex items-start justify-between">
        <span className="text-[11px] text-muted">{label}</span>
        <span className={`grid h-7 w-7 place-items-center rounded-md ${toneClasses[tone]}`}>
          <Icon size={15} />
        </span>
      </div>
      <div className="mt-2 font-mono text-2xl font-semibold text-slate-50">{value}</div>
      {delta ? <div className="mt-1 text-[10px] text-muted">{delta}</div> : null}
    </div>
  )
}
