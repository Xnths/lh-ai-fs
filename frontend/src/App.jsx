import { useState } from 'react'

const CSS = `
  :root {
    --bg: #0F0F0F;
    --surface: #1A1A1A;
    --border: #2A2A2A;
    --text: #E8E8E0;
    --text-muted: #666660;
    --red: #C0392B;
    --amber: #D4850A;
    --green: #2E7D4F;
    --accent: #C0392B;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    min-height: 100vh;
  }

  .app {
    max-width: 860px;
    margin: 0 auto;
    padding: 48px 24px 80px;
  }

  .header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 48px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 24px;
  }

  .header-left {}

  .wordmark {
    font-family: 'Playfair Display', serif;
    font-weight: 700;
    font-size: 28px;
    letter-spacing: 0.04em;
    color: var(--text);
  }

  .wordmark span {
    color: var(--red);
  }

  .subtitle {
    font-size: 12px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-top: 4px;
  }

  .btn-analyze {
    background: var(--red);
    color: #fff;
    border: none;
    padding: 10px 24px;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 13px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border-radius: 2px;
    cursor: pointer;
    transition: opacity 0.15s;
    white-space: nowrap;
  }

  .btn-analyze:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-analyze:not(:disabled):hover {
    opacity: 0.85;
  }

  .empty-state {
    text-align: center;
    padding: 80px 0;
    color: var(--text-muted);
    font-size: 15px;
  }

  .loading-state {
    text-align: center;
    padding: 80px 0;
    color: var(--text-muted);
  }

  .spinner {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 2px solid var(--border);
    border-top-color: var(--red);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-bottom: 16px;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .loading-text {
    display: block;
    font-size: 14px;
  }

  .error-msg {
    background: #1e0a08;
    border-left: 4px solid var(--red);
    padding: 14px 16px;
    color: #e57373;
    font-size: 14px;
    font-family: 'IBM Plex Mono', monospace;
    margin-top: 32px;
    border-radius: 0 2px 2px 0;
  }

  /* Judicial Memo */
  .judicial-memo {
    background: var(--surface);
    border-left: 4px solid var(--amber);
    border-radius: 0 4px 4px 0;
    padding: 24px 28px;
    margin-bottom: 40px;
  }

  .memo-label {
    font-size: 11px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-muted);
    font-family: 'Inter', sans-serif;
    margin-bottom: 14px;
  }

  .memo-body {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 18px;
    line-height: 1.65;
    color: var(--text);
  }

  /* Findings Section */
  .findings-section {
    margin-bottom: 40px;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  .section-title {
    font-size: 11px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-muted);
    font-family: 'Inter', sans-serif;
  }

  .section-count {
    font-size: 12px;
    color: var(--text-muted);
    font-family: 'IBM Plex Mono', monospace;
  }

  /* Finding Card */
  .finding-card {
    background: var(--surface);
    border-radius: 0 4px 4px 0;
    padding: 18px 20px;
    margin-bottom: 10px;
    position: relative;
  }

  .finding-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    border-radius: 4px 0 0 4px;
  }

  .finding-card.severity-high::before,
  .finding-card.verdict-not_supported::before,
  .finding-card.verdict-inaccurate::before { background: var(--red); }

  .finding-card.severity-medium::before,
  .finding-card.verdict-could_not_verify::before { background: var(--amber); }

  .finding-card.severity-low::before,
  .finding-card.verdict-supported::before,
  .finding-card.verdict-accurate::before { background: var(--border); }

  .card-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 10px;
  }

  .card-title {
    font-size: 14px;
    font-weight: 500;
    color: var(--text);
    font-family: 'Inter', sans-serif;
    flex: 1;
    line-height: 1.4;
  }

  .badge {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 2px;
    white-space: nowrap;
    font-family: 'Inter', sans-serif;
    flex-shrink: 0;
  }

  .badge-red    { background: var(--red); color: #fff; }
  .badge-amber  { background: var(--amber); color: #111; }
  .badge-green  { background: var(--green); color: #fff; }
  .badge-gray   { background: #333; color: var(--text-muted); }

  .card-meta {
    font-size: 12px;
    color: var(--text-muted);
    font-family: 'Inter', sans-serif;
    margin-bottom: 8px;
  }

  .card-quote {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #AAA;
    line-height: 1.6;
    background: #111;
    border-radius: 2px;
    padding: 10px 12px;
    margin-top: 8px;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .card-reasoning {
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.55;
    margin-top: 8px;
    font-family: 'IBM Plex Mono', monospace;
  }

  .confidence-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
  }

  .confidence-label {
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
    font-family: 'Inter', sans-serif;
    white-space: nowrap;
  }

  .confidence-pct {
    font-size: 12px;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
  }

  .confidence-pct.conf-high  { color: #2E7D4F; }
  .confidence-pct.conf-mid   { color: #D4850A; }
  .confidence-pct.conf-low   { color: #C0392B; }

  .confidence-note {
    font-size: 11px;
    color: var(--text-muted);
    font-family: 'IBM Plex Mono', monospace;
    margin-top: 4px;
    line-height: 1.5;
  }
`

function ConfidenceDisplay({ confidence, confidenceReasoning }) {
  if (confidence == null) return null
  const pct = Math.round(confidence * 100)
  const cls = confidence >= 0.8 ? 'conf-high' : confidence >= 0.5 ? 'conf-mid' : 'conf-low'
  return (
    <div>
      <div className="confidence-row">
        <span className="confidence-label">Confidence</span>
        <span className={`confidence-pct ${cls}`}>{pct}%</span>
      </div>
      {confidenceReasoning && <div className="confidence-note">{confidenceReasoning}</div>}
    </div>
  )
}

function verdictBadge(verdict) {
  const map = {
    not_supported:     { cls: 'badge-red',   label: 'Not Supported' },
    inaccurate:        { cls: 'badge-red',   label: 'Inaccurate' },
    could_not_verify:  { cls: 'badge-amber', label: 'Unverified' },
    supported:         { cls: 'badge-green', label: 'Supported' },
    accurate:          { cls: 'badge-green', label: 'Accurate' },
    high:              { cls: 'badge-red',   label: 'High' },
    medium:            { cls: 'badge-amber', label: 'Medium' },
    low:               { cls: 'badge-gray',  label: 'Low' },
  }
  const entry = map[verdict?.toLowerCase()] ?? { cls: 'badge-gray', label: verdict ?? '—' }
  return <span className={`badge ${entry.cls}`}>{entry.label}</span>
}

function cardClass(item) {
  const v = (item.verdict ?? item.severity ?? '').toLowerCase()
  if (['not_supported', 'inaccurate', 'high'].includes(v)) return 'finding-card severity-high'
  if (['could_not_verify', 'medium'].includes(v)) return 'finding-card severity-medium'
  return 'finding-card severity-low'
}

function CitationCard({ item }) {
  return (
    <div className={cardClass(item)}>
      <div className="card-top">
        <div className="card-title">{item.citation ?? item.case_name ?? item.authority ?? '—'}</div>
        {verdictBadge(item.verdict ?? item.assessment)}
      </div>
      {item.proposition && <div className="card-meta">Proposition: {item.proposition}</div>}
      {item.reasoning && <div className="card-reasoning">{item.reasoning}</div>}
      <ConfidenceDisplay confidence={item.confidence} confidenceReasoning={item.confidence_reasoning} />
    </div>
  )
}

function QuoteCard({ item }) {
  return (
    <div className={cardClass(item)}>
      <div className="card-top">
        <div className="card-title">{item.citation ?? item.case_name ?? item.authority ?? '—'}</div>
        {verdictBadge(item.verdict ?? item.accuracy)}
      </div>
      {item.quoted_text && <div className="card-quote">"{item.quoted_text}"</div>}
      {item.actual_text && (
        <>
          <div className="card-meta" style={{ marginTop: 10 }}>Actual text:</div>
          <div className="card-quote">"{item.actual_text}"</div>
        </>
      )}
      {item.issue && <div className="card-reasoning">{item.issue}</div>}
      <ConfidenceDisplay confidence={item.confidence} confidenceReasoning={item.confidence_reasoning} />
    </div>
  )
}

function ContradictionCard({ item }) {
  return (
    <div className={cardClass(item)}>
      <div className="card-top">
        <div className="card-title">{item.claim ?? item.fact ?? item.msj_claim ?? '—'}</div>
        {verdictBadge(item.severity ?? item.verdict)}
      </div>
      {item.source && <div className="card-meta">Contradicted by: {item.source}</div>}
      {item.contradicting_source && <div className="card-meta">Contradicted by: {item.contradicting_source}</div>}
      {item.contradicting_text && <div className="card-quote">"{item.contradicting_text}"</div>}
      {item.explanation && <div className="card-reasoning">{item.explanation}</div>}
      <ConfidenceDisplay confidence={item.confidence} confidenceReasoning={item.confidence_reasoning} />
    </div>
  )
}

function FindingsSection({ title, items, CardComponent }) {
  if (!items?.length) return null
  return (
    <div className="findings-section">
      <div className="section-header">
        <div className="section-title">{title}</div>
        <div className="section-count">{items.length} found</div>
      </div>
      {items.map((item, i) => <CardComponent key={i} item={item} />)}
    </div>
  )
}

export default function App() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const analyze = async () => {
    setLoading(true)
    setError(null)
    setReport(null)
    try {
      const res = await fetch('http://localhost:8002/analyze', { method: 'POST' })
      if (!res.ok) throw new Error(`Server responded with ${res.status}`)
      const data = await res.json()
      setReport(data.report ?? data)
    } catch (e) {
      setError(e.message ?? 'Pipeline failed. Check backend.')
    } finally {
      setLoading(false)
    }
  }

  const citations   = report?.citations ?? report?.citation_verification ?? []
  const quotes      = report?.quotes ?? report?.quote_accuracy ?? []
  const contradictions = report?.contradictions ?? report?.factual_contradictions ?? []
  const memo        = report?.judicial_memo ?? report?.memo ?? null

  return (
    <>
      <style>{CSS}</style>
      <div className="app">
        <header className="header">
          <div className="header-left">
            <div className="wordmark">BS<span> DETECTOR</span></div>
            <div className="subtitle">Legal brief verification</div>
          </div>
          <button className="btn-analyze" onClick={analyze} disabled={loading}>
            {loading ? 'Running…' : 'Analyze'}
          </button>
        </header>

        {error && <div className="error-msg">Error: {error}</div>}

        {loading && (
          <div className="loading-state">
            <span className="spinner" />
            <span className="loading-text">Running pipeline… this may take a few minutes.</span>
          </div>
        )}

        {!loading && !report && !error && (
          <div className="empty-state">Upload a brief to begin.</div>
        )}

        {report && !loading && (
          <>
            {memo && (
              <div className="judicial-memo">
                <div className="memo-label">Judicial Memo</div>
                <div className="memo-body">{typeof memo === 'string' ? memo : memo.summary ?? memo.text ?? JSON.stringify(memo)}</div>
              </div>
            )}

            <FindingsSection
              title="Factual Contradictions"
              items={contradictions}
              CardComponent={ContradictionCard}
            />

            <FindingsSection
              title="Quote Accuracy"
              items={quotes}
              CardComponent={QuoteCard}
            />

            <FindingsSection
              title="Citation Verification"
              items={citations}
              CardComponent={CitationCard}
            />
          </>
        )}
      </div>
    </>
  )
}
