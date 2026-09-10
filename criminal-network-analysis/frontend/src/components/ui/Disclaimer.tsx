import { ShieldAlert } from 'lucide-react'

export default function Disclaimer({ text }: { text?: string }) {
  return (
    <div className="mt-6 flex items-start gap-2 border-t border-line pt-3 text-[11px] leading-relaxed text-muted">
      <ShieldAlert size={14} className="mt-0.5 shrink-0 text-accent2" />
      <span>
        {text ||
          'This platform is an investigative decision-support system. AI-generated findings are potential connections, risk indicators, or analytical leads only, never proof of guilt, and require investigator verification.'}
      </span>
    </div>
  )
}
