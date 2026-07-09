import { useState, useEffect } from 'react'

export default function SourceFilter({ selectedSource, onSourceChange }) {
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/ingest/list')
      .then(r => r.json())
      .then(data => setSources((data.ingestions || []).filter(i => i.status === 'complete')))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <p className="text-xs font-mono text-claude-text-tertiary">Loading sources…</p>
  )

  return (
    <div>
      <label className="block text-xs font-semibold text-claude-text-secondary mb-1.5 uppercase tracking-wider">
        Filter by Source
      </label>
      <select
        value={selectedSource || 'all'}
        onChange={e => onSourceChange(e.target.value === 'all' ? null : e.target.value)}
        className="w-full px-3 py-2 bg-claude-bg border border-claude-border rounded-xl text-sm text-claude-text focus:outline-none transition-all"
        style={{ '--tw-ring-color': '#D97757' }}
        onFocus={e => e.target.style.boxShadow = '0 0 0 2px #D9775740'}
        onBlur={e => e.target.style.boxShadow = 'none'}>
        <option value="all">All Sources</option>
        {sources.map(s => (
          <option key={s.ingestion_id} value={s.ingestion_id}>
            {s.source_name} ({s.total_docs} docs)
          </option>
        ))}
      </select>
      {sources.length === 0 && (
        <p className="mt-1.5 text-xs font-mono text-claude-text-tertiary">No sources yet.</p>
      )}
    </div>
  )
}
