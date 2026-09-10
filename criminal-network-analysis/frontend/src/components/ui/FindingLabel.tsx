const STYLES: Record<string, string> = {
  'Potential connection': 'text-info border-info/40 bg-info/10',
  'Risk indicator': 'text-accent2 border-accent2/40 bg-accent2/10',
  'Analytical lead': 'text-accent border-accent/40 bg-accent/10',
  'Requires investigator verification': 'text-danger border-danger/40 bg-danger/10',
}

export default function FindingLabel({ label }: { label?: string }) {
  if (!label) return null
  return <span className={`badge ${STYLES[label] || STYLES['Analytical lead']}`}>{label}</span>
}
