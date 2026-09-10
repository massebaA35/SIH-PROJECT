import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { FileDown, FileText, Loader2 } from 'lucide-react'
import { api } from '../services/api'
import type { Case } from '../types'
import FindingLabel from '../components/ui/FindingLabel'
import SeverityBadge from '../components/ui/SeverityBadge'
import Disclaimer from '../components/ui/Disclaimer'

export default function Reports() {
  const [params] = useSearchParams()
  const [cases, setCases] = useState<Case[]>([])
  const [caseId, setCaseId] = useState(params.get('case_id') || '')
  const [notes, setNotes] = useState('')
  const [report, setReport] = useState<any>(null)
  const [generating, setGenerating] = useState(false)
  const [downloadingPdf, setDownloadingPdf] = useState(false)

  useEffect(() => {
    api.get('/cases', { params: { page_size: 100 } }).then((res) => {
      setCases(res.data.items)
      if (!caseId && res.data.items.length) setCaseId(res.data.items[0].id)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const generate = async () => {
    if (!caseId) return
    setGenerating(true)
    try {
      const res = await api.post('/reports', { case_id: caseId, investigator_notes: notes, format: 'json' })
      setReport(res.data)
    } finally {
      setGenerating(false)
    }
  }

  const downloadPdf = async () => {
    if (!caseId) return
    setDownloadingPdf(true)
    try {
      const res = await api.post('/reports', { case_id: caseId, investigator_notes: notes, format: 'pdf' }, { responseType: 'blob' })
      const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = url
      link.download = `${caseId}-report.pdf`
      link.click()
      URL.revokeObjectURL(url)
    } finally {
      setDownloadingPdf(false)
    }
  }

  return (
    <div>
      <div className="mb-5">
        <div className="text-[10px] uppercase tracking-widest text-muted">NCAS workspace / reporting</div>
        <h1 className="mt-1 text-2xl font-bold">Investigation reports</h1>
        <p className="text-xs text-muted">Structured, exportable report combining case data, network statistics, and AI-assisted observations.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[320px_1fr]">
        <div className="panel space-y-3 p-4">
          <div>
            <label className="mb-1 block text-[10px] uppercase text-muted">Case</label>
            <select className="input w-full" value={caseId} onChange={(e) => setCaseId(e.target.value)}>
              {cases.map((c) => <option key={c.id} value={c.id}>{c.id} · {c.title}</option>)}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-[10px] uppercase text-muted">Investigator notes</label>
            <textarea
              className="input h-28 w-full resize-none"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add context an investigator wants included in the report..."
            />
          </div>
          <button className="btn-primary w-full justify-center" onClick={generate} disabled={generating}>
            {generating ? <Loader2 size={14} className="animate-spin" /> : <FileText size={14} />}
            Generate report
          </button>
          <button className="btn w-full justify-center" onClick={downloadPdf} disabled={downloadingPdf}>
            {downloadingPdf ? <Loader2 size={14} className="animate-spin" /> : <FileDown size={14} />}
            Download PDF
          </button>
        </div>

        <div className="panel p-5">
          {!report ? (
            <p className="text-xs text-muted">Generate a report to preview it here.</p>
          ) : (
            <div className="space-y-5 text-xs">
              <div className="rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-[11px] font-semibold text-danger">
                {report.report_label}
              </div>

              <section>
                <h2 className="mb-1 text-sm font-semibold">01 · Case information</h2>
                <p className="leading-relaxed text-slate-300">
                  This report covers <strong>{report.case_information.title}</strong> ({report.case_id}), currently{' '}
                  {report.case_information.status.toLowerCase()} with {report.case_information.priority} priority and a{' '}
                  {report.case_information.risk_level.toLowerCase()} risk rating. Assigned to {report.case_information.assigned_investigator}.
                </p>
                <p className="mt-1 text-muted">{report.case_information.description}</p>
              </section>

              <section>
                <h2 className="mb-1 text-sm font-semibold">02 · Network statistics</h2>
                <p className="text-slate-300">
                  {report.network_statistics.entities_tracked} entities tracked across {report.network_statistics.relationships_recorded}{' '}
                  relationships, forming {report.network_statistics.communities_detected} detected communities.
                </p>
                {report.network_statistics.bridge_entities.length > 0 && (
                  <p className="mt-1 text-muted">Bridge entities: {report.network_statistics.bridge_entities.join(', ')}</p>
                )}
              </section>

              <section>
                <h2 className="mb-2 text-sm font-semibold">03 · AI-assisted analytical observations</h2>
                <div className="space-y-2">
                  {report.ai_analytical_observations.map((o: any) => (
                    <div key={o.entity_id} className="border-l-2 border-accent2 bg-white/5 px-3 py-2">
                      <div className="flex items-center justify-between">
                        <strong>{o.entity_label}</strong>
                        <FindingLabel label={o.finding_label} />
                      </div>
                      <p className="mt-0.5 text-muted">{o.analytical_interpretation} ({o.network_connectivity_score}/100)</p>
                    </div>
                  ))}
                </div>
              </section>

              <section>
                <h2 className="mb-2 text-sm font-semibold">04 · Alerts</h2>
                {report.alerts.length === 0 ? (
                  <p className="text-muted">No alerts recorded for this case.</p>
                ) : (
                  <div className="space-y-1.5">
                    {report.alerts.map((a: any) => (
                      <div key={a.id} className="flex items-center gap-2">
                        <SeverityBadge severity={a.severity} />
                        <FindingLabel label={a.label} />
                        <span>{a.title}</span>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              <section>
                <h2 className="mb-1 text-sm font-semibold">05 · Evidence references</h2>
                <ul className="list-disc space-y-1 pl-4 text-muted">
                  {report.evidence_references.map((e: any) => (
                    <li key={e.id}><strong className="text-slate-200">{e.id}:</strong> {e.description}</li>
                  ))}
                  {report.evidence_references.length === 0 && <li>No evidence records for this case.</li>}
                </ul>
              </section>

              {report.investigator_notes && (
                <section>
                  <h2 className="mb-1 text-sm font-semibold">Investigator notes</h2>
                  <p className="text-slate-300">{report.investigator_notes}</p>
                </section>
              )}

              <Disclaimer text={report.disclaimer} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
