import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search, ChevronLeft, ChevronRight, ChevronRight as Arrow, FileText, Sparkles,
  AlertCircle, CheckCircle, RefreshCcw, Layers, Upload, XCircle, Eye, EyeOff,
} from 'lucide-react'
import { api } from '../services/api'
import Disclaimer from '../components/ui/Disclaimer'

const EXTRACTION_TYPE_FILTERS = ['ALL', 'PERSON', 'ORGANIZATION', 'LOCATION', 'VEHICLE', 'PHONE', 'CASE', 'DATE', 'CRIME_CATEGORY']

const TYPE_COLOR: Record<string, string> = {
  PERSON: 'bg-accent', ORGANIZATION: 'bg-accent2', VEHICLE: 'bg-info',
  PHONE: 'bg-purple-400', LOCATION: 'bg-danger', ACCOUNT: 'bg-emerald-400',
  FINANCIAL_ENTITY: 'bg-emerald-500', EMAIL: 'bg-blue-400', CASE: 'bg-amber-400',
  DATE: 'bg-indigo-400', FACILITY: 'bg-orange-400', CRIME_CATEGORY: 'bg-rose-400',
}

const SAMPLE_TEXT = `Person A met Person B at Kochi on 12 August.
They used vehicle KL-07-AB-1234 and communicated using phone number +91 98765 43210.
Person A transferred Rs. 50,000 to Coastal Traders Pvt Ltd via account ACC-987654321.`

export default function Entities() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'directory' | 'extraction'>('directory')

  // Directory state
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [type, setType] = useState('')
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 15
  const [loading, setLoading] = useState(true)

  // Extraction state
  const [rawText, setRawText] = useState('')
  const [extracting, setExtracting] = useState(false)
  const [extractionResult, setExtractionResult] = useState<any>(null)
  const [uploadedFileName, setUploadedFileName] = useState('')
  const [uploadError, setUploadError] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const MAX_UPLOAD_SIZE = 2 * 1024 * 1024
  const [extractionTypeFilter, setExtractionTypeFilter] = useState('ALL')
  const [showRejected, setShowRejected] = useState(false)

  useEffect(() => {
    if (activeTab !== 'directory') return
    const handle = setTimeout(() => {
      setLoading(true)
      api
        .get('/entities', { params: { type: type || undefined, q, page, page_size: pageSize } })
        .then((res) => {
          setItems(res.data.items)
          setTotal(res.data.total)
        })
        .finally(() => setLoading(false))
    }, 250)
    return () => clearTimeout(handle)
  }, [type, q, page, activeTab])

  const handleFirFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    setUploadError('')
    const looksLikeText = file.name.toLowerCase().endsWith('.txt') || file.type === 'text/plain'
    if (!looksLikeText) {
      setUploadError('Only plain text (.txt) files are supported for FIR upload.')
      return
    }
    if (file.size > MAX_UPLOAD_SIZE) {
      setUploadError('File is too large. Maximum size is 2 MB for text FIR uploads.')
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      setRawText(String(reader.result || ''))
      setUploadedFileName(file.name)
      setExtractionResult(null)
    }
    reader.onerror = () => setUploadError('Could not read the selected file.')
    reader.readAsText(file)
  }

  const handleExtract = async () => {
    if (!rawText.trim() || extracting) return
    setExtracting(true)
    try {
      const res = await api.post('/analyze/text', { text: rawText })
      setExtractionResult(res.data)
    } finally {
      setExtracting(false)
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div>
      <div className="mb-5 flex items-end justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-muted">NCAS workspace / entity intelligence</div>
          <h1 className="mt-1 text-2xl font-bold">Entities & Extraction</h1>
          <p className="text-xs text-muted">Entity directory and offline NLP extraction from free text or uploaded FIR files.</p>
        </div>
      </div>

      <div className="mb-4 flex gap-2 border-b border-line">
        <button
          onClick={() => setActiveTab('directory')}
          className={`flex items-center gap-2 border-b-2 px-3 py-2 text-xs font-medium transition ${
            activeTab === 'directory' ? 'border-accent text-accent' : 'border-transparent text-muted hover:text-slate-200'
          }`}
        >
          <Layers size={14} /> Entity Directory ({total})
        </button>
        <button
          onClick={() => setActiveTab('extraction')}
          className={`flex items-center gap-2 border-b-2 px-3 py-2 text-xs font-medium transition ${
            activeTab === 'extraction' ? 'border-accent text-accent' : 'border-transparent text-muted hover:text-slate-200'
          }`}
        >
          <Sparkles size={14} /> NLP Entity Extraction
        </button>
      </div>

      {activeTab === 'directory' && (
        <>
          <div className="mb-4 flex flex-wrap gap-2">
            <div className="flex items-center gap-2 rounded-md border border-line bg-panel2 px-3 py-2">
              <Search size={13} className="text-muted" />
              <input
                className="w-56 bg-transparent text-xs outline-none placeholder:text-muted"
                placeholder="Search by name or id..."
                value={q}
                onChange={(e) => { setQ(e.target.value); setPage(1) }}
              />
            </div>
            <select className="input" value={type} onChange={(e) => { setType(e.target.value); setPage(1) }}>
              <option value="">All entity types</option>
              {['PERSON', 'ORGANIZATION', 'VEHICLE', 'PHONE', 'LOCATION', 'ACCOUNT'].map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div className="panel overflow-hidden">
            <div className="grid grid-cols-[1.6fr_.8fr_.6fr_16px] gap-4 border-b border-line px-4 py-2.5 text-[10px] uppercase text-muted">
              <span>Entity</span><span>Type</span><span>Connections</span><span />
            </div>
            {loading ? (
              <div className="p-8 text-center text-xs text-muted">Loading entities...</div>
            ) : items.length === 0 ? (
              <div className="p-8 text-center text-xs text-muted">No entities match this search.</div>
            ) : (
              items.map((e) => (
                <button
                  key={e.id}
                  onClick={() => navigate(`/entities/${e.id}`)}
                  className="grid w-full grid-cols-[1.6fr_.8fr_.6fr_16px] items-center gap-4 border-b border-line px-4 py-3 text-left text-xs last:border-0 hover:bg-white/5"
                >
                  <span className="flex items-center gap-2">
                    <span className={`h-2 w-2 rounded-full ${TYPE_COLOR[e.type] || 'bg-muted'}`} />
                    <strong>{e.label}</strong> <small className="font-mono text-muted">{e.id}</small>
                  </span>
                  <span className="text-muted">{e.type}</span>
                  <span>{e.connections}</span>
                  <Arrow size={14} className="text-muted" />
                </button>
              ))
            )}
          </div>

          <div className="mt-3 flex items-center justify-between text-xs text-muted">
            <span>Page {page} of {totalPages}</span>
            <div className="flex gap-2">
              <button className="btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}><ChevronLeft size={13} /> Prev</button>
              <button className="btn" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next <ChevronRight size={13} /></button>
            </div>
          </div>
        </>
      )}

      {activeTab === 'extraction' && (
        <div className="space-y-4">
          <div className="panel p-5">
            <div className="mb-2 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold">Unstructured Intelligence / Text Ingestion</h2>
                <p className="text-xs text-muted">
                  Extracts persons, organizations, locations, vehicles, phones, accounts, cases, and events using offline explainable NLP.
                </p>
              </div>
              <div className="flex gap-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,text/plain"
                  onChange={handleFirFileUpload}
                  className="hidden"
                />
                <button type="button" onClick={() => fileInputRef.current?.click()} className="btn text-xs text-accent">
                  <Upload size={13} /> Upload FIR (.txt)
                </button>
                <button type="button" onClick={() => setRawText(SAMPLE_TEXT)} className="btn text-xs text-accent">
                  <FileText size={13} /> Load Sample Dispatch Text
                </button>
              </div>
            </div>

            {uploadedFileName && !uploadError && (
              <p className="mt-2 flex items-center gap-1.5 text-[11px] text-accent">
                <CheckCircle size={12} /> Loaded "{uploadedFileName}" into the text box below. Review it before extracting.
              </p>
            )}
            {uploadError && (
              <p className="mt-2 flex items-center gap-1.5 text-[11px] text-danger">
                <AlertCircle size={12} /> {uploadError}
              </p>
            )}

            <textarea
              value={rawText}
              onChange={(e) => { setRawText(e.target.value); setUploadedFileName('') }}
              placeholder="Paste interrogation record, witness statement, police report, or FIR text here, or upload a .txt file above..."
              rows={5}
              className="mt-2 w-full rounded-md border border-line bg-panel2 p-3 text-xs text-slate-100 outline-none focus:border-accent"
            />

            <div className="mt-3 flex items-center justify-between">
              <button onClick={handleExtract} disabled={extracting || !rawText.trim()} className="btn-primary">
                {extracting ? <RefreshCcw size={13} className="animate-spin" /> : <Sparkles size={13} />}
                Extract Structured Entities
              </button>
              <span className="text-[11px] text-muted">{rawText.length} characters</span>
            </div>
          </div>

          {extractionResult && (
            <div className="space-y-4">
              {extractionResult.summary && (
                <div className="panel p-4">
                  <h3 className="mb-3 text-xs font-semibold text-slate-100">Extraction validation summary</h3>
                  <div className="mb-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
                    <div className="rounded-md border border-line bg-panel2 p-3">
                      <div className="text-[10px] uppercase text-muted">Entities extracted</div>
                      <div className="mt-1 font-mono text-lg text-accent">{extractionResult.summary.entities_extracted}</div>
                    </div>
                    <div className="rounded-md border border-line bg-panel2 p-3">
                      <div className="text-[10px] uppercase text-muted">Valid entities</div>
                      <div className="mt-1 font-mono text-lg text-accent">{extractionResult.summary.valid_entities}</div>
                    </div>
                    <div className="rounded-md border border-line bg-panel2 p-3">
                      <div className="text-[10px] uppercase text-muted">Rejected candidates</div>
                      <div className="mt-1 font-mono text-lg text-slate-200">{extractionResult.summary.rejected_candidates}</div>
                    </div>
                    <div className="rounded-md border border-line bg-panel2 p-3">
                      <div className="text-[10px] uppercase text-muted">Duplicate relationships merged</div>
                      <div className="mt-1 font-mono text-lg text-slate-200">{extractionResult.summary.duplicate_relationships_merged}</div>
                    </div>
                  </div>
                  <div className="space-y-1">
                    {extractionResult.summary.checks?.map((check: any, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-[11px]">
                        {check.passed
                          ? <CheckCircle size={12} className="shrink-0 text-accent" />
                          : <XCircle size={12} className="shrink-0 text-danger" />}
                        <span className={check.passed ? 'text-slate-300' : 'text-danger'}>{check.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="panel overflow-hidden">
                <div className="flex items-center justify-between border-b border-line bg-panel2 px-4 py-3">
                  <h3 className="text-xs font-semibold text-slate-100">
                    Extracted Entities ({extractionResult.entities?.filter((e: any) => extractionTypeFilter === 'ALL' || e.type === extractionTypeFilter).length || 0})
                  </h3>
                  <select className="input text-[11px]" value={extractionTypeFilter} onChange={(e) => setExtractionTypeFilter(e.target.value)}>
                    {EXTRACTION_TYPE_FILTERS.map((t) => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-[80px_1.5fr_1fr_90px_1fr_100px] gap-3 border-b border-line px-4 py-2 text-[10px] uppercase text-muted">
                  <span>ID</span>
                  <span>Name / Value</span>
                  <span>Type</span>
                  <span>Confidence</span>
                  <span>Source Engine</span>
                  <span>First / Last Seen</span>
                </div>
                <div className="divide-y divide-line">
                  {extractionResult.entities
                    ?.filter((ent: any) => extractionTypeFilter === 'ALL' || ent.type === extractionTypeFilter)
                    .map((ent: any) => (
                    <div
                      key={ent.id}
                      className="grid grid-cols-[80px_1.5fr_1fr_90px_1fr_100px] items-center gap-3 px-4 py-2.5 text-xs hover:bg-white/5"
                    >
                      <span className="font-mono text-[11px] text-muted">{ent.id}</span>
                      <div>
                        <strong className="text-slate-100">{ent.value}</strong>
                        {ent.aliases?.length > 0 && <div className="text-[10px] text-muted">alias: {ent.aliases.join(', ')}</div>}
                      </div>
                      <span className="flex items-center gap-1.5">
                        <span className={`h-2 w-2 rounded-full ${TYPE_COLOR[ent.type] || 'bg-muted'}`} />
                        <span className="text-[11px] text-muted">{ent.type}</span>
                      </span>
                      <span className="font-mono text-[11px] text-accent">
                        {Math.round(ent.confidence * 100)}%
                      </span>
                      <span className="truncate text-[10px] text-muted">{ent.source}</span>
                      <span className="font-mono text-[10px] text-muted">{ent.first_seen}</span>
                    </div>
                  ))}
                  {(!extractionResult.entities || extractionResult.entities.length === 0) && (
                    <div className="p-6 text-center text-xs text-muted">No entities detected in provided text.</div>
                  )}
                </div>
              </div>

              {extractionResult.rejected_candidates?.length > 0 && (
                <div className="panel overflow-hidden">
                  <button
                    onClick={() => setShowRejected((v) => !v)}
                    className="flex w-full items-center justify-between border-b border-line bg-panel2 px-4 py-3 text-left"
                  >
                    <h3 className="flex items-center gap-2 text-xs font-semibold text-slate-100">
                      {showRejected ? <EyeOff size={13} /> : <Eye size={13} />}
                      Show rejected candidates ({extractionResult.rejected_candidates.length})
                    </h3>
                    <span className="text-[10px] text-muted">Phrases the engine considered and intentionally ruled out</span>
                  </button>
                  {showRejected && (
                    <div className="divide-y divide-line">
                      {extractionResult.rejected_candidates.map((r: any, idx: number) => (
                        <div key={idx} className="flex items-center gap-3 px-4 py-2.5 text-xs">
                          <XCircle size={13} className="shrink-0 text-danger" />
                          <strong className="text-slate-200">{r.value}</strong>
                          <span className="rounded bg-white/10 px-2 py-0.5 font-mono text-[10px] text-muted">attempted: {r.attempted_type}</span>
                          <span className="text-muted">{r.reason}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {extractionResult.relationship_leads && extractionResult.relationship_leads.length > 0 && (
                <div className="panel overflow-hidden">
                  <div className="border-b border-line bg-panel2 px-4 py-3">
                    <h3 className="text-xs font-semibold text-slate-100">
                      Potential Relationship Leads ({extractionResult.relationship_leads.length})
                    </h3>
                  </div>
                  <div className="divide-y divide-line">
                    {extractionResult.relationship_leads.map((rel: any, idx: number) => (
                      <div key={idx} className="p-3 text-xs hover:bg-white/5">
                        <div className="flex items-center gap-2">
                          <strong className="text-slate-100">{rel.source}</strong>
                          <span className="rounded bg-white/10 px-2 py-0.5 font-mono text-[10px] text-accent">
                            {rel.relation_type}
                          </span>
                          <strong className="text-slate-100">{rel.target}</strong>
                          <span className={`rounded px-2 py-0.5 text-[10px] ${rel.label === 'Potential Relationship Lead' ? 'bg-accent2/10 text-accent2' : 'bg-accent/10 text-accent'}`}>
                            {rel.label}
                          </span>
                          <span className="ml-auto text-[10px] text-muted">
                            Confidence: {Math.round(rel.confidence * 100)}%{rel.mention_count > 1 ? ` · ${rel.mention_count} mentions` : ''}
                          </span>
                        </div>
                        <div className="mt-1 text-[11px] italic text-muted">
                          "{rel.evidence_sentence}"
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <Disclaimer text={extractionResult.disclaimer} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
