import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search, ChevronLeft, ChevronRight, ChevronRight as Arrow, FileText, Sparkles,
  AlertCircle, CheckCircle, RefreshCcw, Layers, Upload, XCircle, Eye, EyeOff, Network, Loader2,
  FileType, Copy, Fingerprint, FolderSearch, PenSquare,
} from 'lucide-react'
import { api } from '../services/api'
import Disclaimer from '../components/ui/Disclaimer'
import type { Case } from '../types'

const UPLOAD_MAX_SIZE = 2 * 1024 * 1024
const UPLOAD_EXTENSIONS = ['.txt', '.pdf', '.docx']

function fileTypeLabel(filename: string): string {
  const ext = filename.toLowerCase().split('.').pop() || ''
  return { txt: 'Text', pdf: 'PDF', docx: 'Word' }[ext] || ext.toUpperCase()
}

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
  const [intakeMode, setIntakeMode] = useState<'paste' | 'upload'>('paste')
  const [rawText, setRawText] = useState('')
  const [extracting, setExtracting] = useState(false)
  const [extractionResult, setExtractionResult] = useState<any>(null)
  const [extractionTypeFilter, setExtractionTypeFilter] = useState('ALL')
  const [showRejected, setShowRejected] = useState(false)
  const [cases, setCases] = useState<Case[]>([])
  const [commitCaseId, setCommitCaseId] = useState('')
  const [committing, setCommitting] = useState(false)
  const [commitResult, setCommitResult] = useState<any>(null)
  const [commitError, setCommitError] = useState('')

  // Document upload (evidence intake) state
  const uploadInputRef = useRef<HTMLInputElement>(null)
  const [uploadCaseId, setUploadCaseId] = useState('')
  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadIssue, setUploadIssue] = useState<{ kind: 'error' | 'duplicate' | 'unreadable'; message: string; caseId?: string } | null>(null)
  const [evidenceInfo, setEvidenceInfo] = useState<{ evidenceId: string; hash: string; filename: string; caseId: string } | null>(null)
  const [hashCopied, setHashCopied] = useState(false)

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

  useEffect(() => {
    if (activeTab === 'extraction' && cases.length === 0) {
      api.get('/cases', { params: { page_size: 100 } }).then((r) => setCases(r.data.items))
    }
  }, [activeTab])

  const resetUploadResult = () => {
    setUploadIssue(null)
    setEvidenceInfo(null)
    setExtractionResult(null)
    setCommitResult(null)
    setCommitError('')
  }

  const handleEvidenceFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    resetUploadResult()
    const ext = '.' + file.name.toLowerCase().split('.').pop()
    if (!UPLOAD_EXTENSIONS.includes(ext)) {
      setUploadIssue({ kind: 'error', message: `"${file.name}" isn't a supported file type. Upload a .txt, .pdf, or .docx document.` })
      setPendingFile(null)
      return
    }
    if (file.size > UPLOAD_MAX_SIZE) {
      setUploadIssue({ kind: 'error', message: `"${file.name}" is too large. Maximum size is 2 MB.` })
      setPendingFile(null)
      return
    }
    setPendingFile(file)
  }

  const handleEvidenceUpload = async () => {
    if (!uploadCaseId || !pendingFile || uploading) return
    setUploading(true)
    resetUploadResult()
    const form = new FormData()
    form.append('case_id', uploadCaseId)
    form.append('file', pendingFile)
    try {
      const res = await api.post('/evidence/upload', form)
      setExtractionResult(res.data)
      setEvidenceInfo({
        evidenceId: res.data.evidence_id,
        hash: res.data.sha256_hash,
        filename: pendingFile.name,
        caseId: uploadCaseId,
      })
      setCommitCaseId(uploadCaseId)
    } catch (err: any) {
      const status = err.response?.status
      const detail = err.response?.data?.detail
      if (status === 409) {
        setUploadIssue({
          kind: 'duplicate',
          message: `This exact document is already recorded as evidence in this case set.`,
          caseId: typeof detail === 'object' ? detail.case_id : undefined,
        })
      } else if (status === 422) {
        setUploadIssue({
          kind: 'unreadable',
          message: 'No extractable text was found in this file. Scanned or image-only documents aren’t supported yet — try pasting the text instead.',
        })
      } else {
        setUploadIssue({ kind: 'error', message: (typeof detail === 'string' && detail) || 'Could not upload this document. Check the file and try again.' })
      }
    } finally {
      setUploading(false)
    }
  }

  const copyHash = () => {
    if (!evidenceInfo) return
    navigator.clipboard.writeText(evidenceInfo.hash).then(() => {
      setHashCopied(true)
      setTimeout(() => setHashCopied(false), 1500)
    })
  }

  const handleExtract = async () => {
    if (!rawText.trim() || extracting) return
    setExtracting(true)
    setCommitResult(null)
    setCommitError('')
    try {
      const res = await api.post('/analyze/text', { text: rawText })
      setExtractionResult(res.data)
    } finally {
      setExtracting(false)
    }
  }

  const handleCommit = async () => {
    if (!commitCaseId || !extractionResult || committing) return
    setCommitting(true)
    setCommitError('')
    try {
      const res = await api.post('/analyze/commit', {
        case_id: commitCaseId,
        entities: extractionResult.entities,
        relationship_leads: extractionResult.relationship_leads,
      })
      setCommitResult(res.data)
    } catch (err: any) {
      setCommitError(err.response?.data?.detail || 'Could not add this extraction to the case network. Only Administrators and Investigators can confirm entities into a case.')
    } finally {
      setCommitting(false)
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
          <div className="inline-flex rounded-md border border-line bg-panel2 p-0.5">
            <button
              onClick={() => { setIntakeMode('paste'); resetUploadResult(); setCommitCaseId('') }}
              className={`flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-medium transition ${
                intakeMode === 'paste' ? 'bg-accent text-[#04211d]' : 'text-muted hover:text-slate-200'
              }`}
            >
              <PenSquare size={12} /> Paste text
            </button>
            <button
              onClick={() => { setIntakeMode('upload'); setExtractionResult(null); setCommitResult(null); setCommitError('') }}
              className={`flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-medium transition ${
                intakeMode === 'upload' ? 'bg-accent text-[#04211d]' : 'text-muted hover:text-slate-200'
              }`}
            >
              <FolderSearch size={12} /> Upload document
            </button>
          </div>

          {intakeMode === 'paste' && (
            <div className="panel p-5">
              <div className="mb-2 flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold">Unstructured Intelligence / Text Ingestion</h2>
                  <p className="text-xs text-muted">
                    Extracts persons, organizations, locations, vehicles, phones, accounts, cases, and events using offline explainable NLP.
                  </p>
                </div>
                <button type="button" onClick={() => setRawText(SAMPLE_TEXT)} className="btn text-xs text-accent">
                  <FileText size={13} /> Load Sample Dispatch Text
                </button>
              </div>

              <textarea
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                placeholder="Paste interrogation record, witness statement, police report, or FIR text here..."
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
          )}

          {intakeMode === 'upload' && (
            <div className="panel p-5">
              <div className="mb-3">
                <h2 className="text-sm font-semibold">Evidence Intake</h2>
                <p className="text-xs text-muted">
                  Upload a document (.txt, .pdf, .docx) as case evidence. It's hashed for chain of custody, checked against
                  previously recorded evidence, then run through the same offline extraction engine as pasted text.
                </p>
              </div>

              <div className="flex flex-wrap items-end gap-3">
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] uppercase tracking-widest text-muted">Case</span>
                  <select
                    className="input w-56"
                    value={uploadCaseId}
                    onChange={(e) => { setUploadCaseId(e.target.value); resetUploadResult(); setPendingFile(null) }}
                  >
                    <option value="">Select a case</option>
                    {cases.map((c) => <option key={c.id} value={c.id}>{c.id} · {c.title}</option>)}
                  </select>
                </label>

                <input
                  ref={uploadInputRef}
                  type="file"
                  accept=".txt,.pdf,.docx"
                  onChange={handleEvidenceFileSelect}
                  className="hidden"
                />
                <button
                  type="button"
                  onClick={() => uploadInputRef.current?.click()}
                  disabled={!uploadCaseId}
                  className="btn text-xs text-accent disabled:cursor-not-allowed disabled:opacity-40"
                  title={!uploadCaseId ? 'Select a case first' : undefined}
                >
                  <Upload size={13} /> Select file
                </button>

                {pendingFile && (
                  <span className="flex items-center gap-1.5 rounded-md border border-line bg-panel2 px-2.5 py-1.5 text-[11px] text-slate-200">
                    <FileType size={12} className="text-muted" /> {pendingFile.name}
                    <span className="text-muted">· {fileTypeLabel(pendingFile.name)}</span>
                  </span>
                )}

                <button
                  onClick={handleEvidenceUpload}
                  disabled={!uploadCaseId || !pendingFile || uploading}
                  className="btn-primary"
                >
                  {uploading ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
                  {uploading ? 'Hashing & extracting…' : 'Upload & extract'}
                </button>
              </div>

              {uploadIssue && (
                <div
                  className={`mt-3 flex items-start gap-2 rounded-md border p-3 text-[11px] ${
                    uploadIssue.kind === 'error'
                      ? 'border-danger/30 bg-danger/10 text-danger'
                      : 'border-accent2/30 bg-accent2/10 text-accent2'
                  }`}
                >
                  <AlertCircle size={13} className="mt-0.5 shrink-0" />
                  <span>{uploadIssue.message}</span>
                </div>
              )}

              {evidenceInfo && (
                <div className="mt-4 rounded-md border border-accent/30 bg-panel2 p-3">
                  <div className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold text-accent">
                    <CheckCircle size={13} /> Evidence recorded
                  </div>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[11px] sm:grid-cols-4">
                    <div>
                      <div className="text-[10px] uppercase text-muted">Evidence ID</div>
                      <div className="font-mono text-slate-200">{evidenceInfo.evidenceId}</div>
                    </div>
                    <div>
                      <div className="text-[10px] uppercase text-muted">Case</div>
                      <div className="text-slate-200">{evidenceInfo.caseId}</div>
                    </div>
                    <div>
                      <div className="text-[10px] uppercase text-muted">File</div>
                      <div className="truncate text-slate-200">{evidenceInfo.filename}</div>
                    </div>
                    <div>
                      <div className="text-[10px] uppercase text-muted">SHA-256 (chain of custody)</div>
                      <button onClick={copyHash} className="flex items-center gap-1 font-mono text-slate-200 hover:text-accent" title="Copy full hash">
                        <Fingerprint size={11} className="shrink-0 text-muted" />
                        {evidenceInfo.hash.slice(0, 12)}…
                        <Copy size={11} className="shrink-0" />
                        {hashCopied && <span className="text-accent">copied</span>}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {extractionResult && (
            <div className="space-y-4">
              <div className="panel p-4">
                <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-slate-200">
                  <Network size={14} className="text-accent" /> Add to case network
                </div>
                <p className="mb-3 text-[11px] text-muted">
                  Extraction alone never changes any case record. Review the entities and relationships above, then
                  {evidenceInfo ? ' confirm them into this evidence’s case network' : ' pick a case to confirm them into its network graph'},
                  this is the step that makes them appear in Network Analysis.
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  {evidenceInfo ? (
                    <span className="input flex items-center gap-1.5 text-slate-200">
                      <FolderSearch size={12} className="text-muted" /> {evidenceInfo.caseId}
                    </span>
                  ) : (
                    <select className="input" value={commitCaseId} onChange={(e) => { setCommitCaseId(e.target.value); setCommitResult(null); setCommitError('') }}>
                      <option value="">Select a case</option>
                      {cases.map((c) => <option key={c.id} value={c.id}>{c.id} · {c.title}</option>)}
                    </select>
                  )}
                  <button className="btn-primary" disabled={!commitCaseId || committing} onClick={handleCommit}>
                    {committing ? <Loader2 size={13} className="animate-spin" /> : <Network size={13} />}
                    Confirm & add to case network
                  </button>
                  {commitResult && (
                    <button className="btn text-xs" onClick={() => navigate(`/cases/${commitResult.case_id}`)}>
                      View case network <ChevronRight size={13} />
                    </button>
                  )}
                </div>
                {commitError && <p className="mt-3 text-xs text-danger">{commitError}</p>}
                {commitResult && (
                  <div className="mt-3 rounded-md border border-accent/30 bg-accent/10 p-3 text-[11px] text-accent">
                    Added to {commitResult.case_id}: {commitResult.entities_created} new entit{commitResult.entities_created === 1 ? 'y' : 'ies'} created,{' '}
                    {commitResult.entities_matched} matched to existing records, {commitResult.relationships_created} relationship(s) added
                    {commitResult.relationships_skipped > 0 ? ` (${commitResult.relationships_skipped} skipped, endpoints not resolved)` : ''}.
                    {commitResult.skipped_entity_types?.length > 0 && ` Not persisted as graph nodes: ${commitResult.skipped_entity_types.join(', ')}.`}
                  </div>
                )}
              </div>

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
