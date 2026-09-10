const STYLES: Record<string, string> = {
  LOW: 'text-info border-info/40 bg-info/10',
  MEDIUM: 'text-accent2 border-accent2/40 bg-accent2/10',
  HIGH: 'text-danger border-danger/40 bg-danger/10',
  CRITICAL: 'text-white border-danger bg-danger/60',
}

export default function SeverityBadge({ severity }: { severity: string }) {
  return <span className={`badge ${STYLES[severity] || STYLES.MEDIUM}`}>{severity}</span>
}
