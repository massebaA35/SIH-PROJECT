import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, Send, Loader2, Lightbulb } from 'lucide-react'
import { api } from '../services/api'
import Disclaimer from '../components/ui/Disclaimer'

const SUGGESTED_PROMPTS = [
  'What entities are connected to CASE-1001?',
  'Show the strongest connections of PERSON-101.',
  'Which entities appear in multiple cases?',
  'Why is PERSON-101 flagged?',
  'Summarize the timeline of CASE-1001.',
  'Find hidden links between PERSON-101 and PERSON-102.',
]

interface RelatedEntity { id: string; label: string }
interface SourceRecord { id: string; type: string; description: string }
interface CopilotResponse {
  question: string; answer: string; reasoning: string[]; related_entities: RelatedEntity[]
  related_cases: string[]; source_records: SourceRecord[]; interpretation: string; disclaimer: string
}

export default function Copilot() {
  const navigate = useNavigate()
  const [question, setQuestion] = useState('')
  const [history, setHistory] = useState<CopilotResponse[]>([])
  const [loading, setLoading] = useState(false)

  const ask = async (q: string) => {
    if (!q.trim() || loading) return
    setLoading(true)
    try {
      const res = await api.post('/assistant/ask', { question: q })
      setHistory((prev) => [res.data, ...prev])
      setQuestion('')
    } finally {
      setLoading(false)
    }
  }

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    ask(question)
  }

  return (
    <div>
      <div className="mb-5">
        <div className="text-[10px] uppercase tracking-widest text-muted">NCAS workspace / explainable investigation copilot</div>
        <h1 className="mt-1 text-2xl font-bold">Investigation Copilot</h1>
        <p className="text-xs text-muted">Answers strictly from the available dataset. Every response cites the entities, cases, and records behind it.</p>
      </div>

      <form onSubmit={onSubmit} className="panel mb-4 flex items-center gap-2 p-3">
        <Sparkles size={16} className="shrink-0 text-accent" />
        <input
          className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted"
          placeholder="Ask about a case, entity, alert, or hidden link..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          autoFocus
        />
        <button className="btn-primary" disabled={loading || !question.trim()}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          Ask
        </button>
      </form>

      {history.length === 0 && (
        <div className="panel mb-4 p-4">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-slate-200">
            <Lightbulb size={13} className="text-accent2" /> Suggested prompts
          </div>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_PROMPTS.map((p) => (
              <button key={p} onClick={() => ask(p)} className="btn text-[11px]">{p}</button>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-4">
        {history.map((r, idx) => (
          <div key={idx} className="panel p-5">
            <div className="mb-3 border-b border-line pb-3">
              <div className="text-[10px] uppercase text-muted">Question</div>
              <div className="mt-1 text-sm font-medium text-slate-200">{r.question}</div>
            </div>

            <div className="mb-3">
              <div className="text-[10px] uppercase text-accent">Answer</div>
              <p className="mt-1 text-sm text-slate-100">{r.answer}</p>
              {r.interpretation && (
                <p className="mt-2 rounded-md border border-accent2/30 bg-accent2/10 px-3 py-2 text-xs text-accent2">
                  {r.interpretation}
                </p>
              )}
            </div>

            {r.reasoning.length > 0 && (
              <div className="mb-3">
                <div className="text-[10px] uppercase text-muted">Reasoning / supporting data</div>
                <ul className="mt-1 list-disc space-y-1 pl-4 text-xs text-slate-300">
                  {r.reasoning.filter(Boolean).map((line, i) => <li key={i}>{line}</li>)}
                </ul>
              </div>
            )}

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              {r.related_entities.length > 0 && (
                <div>
                  <div className="mb-1 text-[10px] uppercase text-muted">Related entities</div>
                  <div className="flex flex-wrap gap-1">
                    {r.related_entities.map((e) => (
                      <button key={e.id} onClick={() => navigate(`/entities/${e.id}`)} className="badge border-line text-slate-300 hover:border-accent hover:text-accent">
                        {e.label} <span className="ml-1 font-mono text-[9px] text-muted">{e.id}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {r.related_cases.length > 0 && (
                <div>
                  <div className="mb-1 text-[10px] uppercase text-muted">Related cases</div>
                  <div className="flex flex-wrap gap-1">
                    {r.related_cases.map((c) => (
                      <button key={c} onClick={() => navigate(`/cases/${c}`)} className="badge border-line text-slate-300 hover:border-accent hover:text-accent">{c}</button>
                    ))}
                  </div>
                </div>
              )}
              {r.source_records.length > 0 && (
                <div>
                  <div className="mb-1 text-[10px] uppercase text-muted">Source records</div>
                  <div className="space-y-1">
                    {r.source_records.slice(0, 5).map((s) => (
                      <div key={s.id} className="truncate text-[10px] text-muted"><span className="font-mono text-slate-300">{s.id}</span> · {s.description}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <p className="mt-4 border-t border-line pt-3 text-[10px] text-muted">{r.disclaimer}</p>
          </div>
        ))}
      </div>

      {history.length === 0 && <Disclaimer />}
    </div>
  )
}
