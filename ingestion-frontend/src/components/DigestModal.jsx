import { useState, useEffect } from 'react'

export default function DigestModal({ ingestionId, onClose }) {
  const [digest, setDigest] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { generate() }, [])

  const generate = async () => {
    setLoading(true)
    try {
      const r = await fetch('/api/digest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ingestion_id: ingestionId, days_back: 7 }),
      })
      if (!r.ok) throw new Error('Failed')
      setDigest(await r.json())
    } catch {
      alert('Failed to generate digest')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-claude-surface border border-claude-border rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto custom-scrollbar shadow-claude-xl">
        {/* Header */}
        <div className="sticky top-0 bg-claude-surface border-b border-claude-border px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <h2 className="font-display text-xl font-bold text-claude-text">Digest</h2>
          <button onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-claude-text-tertiary hover:text-claude-text hover:bg-claude-code-bg transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="text-center py-14">
              <div className="w-10 h-10 border-2 border-claude-border rounded-full mx-auto mb-4"
                style={{ borderTopColor: '#D97757', animation: 'spin 0.8s linear infinite' }} />
              <p className="text-claude-text-secondary text-sm">Generating digest…</p>
            </div>
          ) : digest ? (
            <div>
              <div className="mb-6 pb-5 border-b border-claude-border">
                <h3 className="font-display text-lg font-bold text-claude-text mb-1">{digest.source_name}</h3>
                <p className="text-xs font-mono text-claude-text-tertiary">{digest.period}</p>
              </div>

              {digest.sections?.length > 0 && (
                <div className="space-y-3 mb-6">
                  {digest.sections.map((s, i) => (
                    <div key={i} className="bg-claude-code-bg rounded-xl p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-claude-text text-sm">{s.type}</h4>
                        <span className="text-xs font-mono text-claude-text-tertiary">{s.count} items</span>
                      </div>
                      <p className="text-sm text-claude-text-secondary leading-relaxed">{s.summary}</p>
                    </div>
                  ))}
                </div>
              )}

              {digest.stats && (
                <div className="bg-claude-code-bg rounded-xl p-4 mb-6">
                  <h4 className="font-semibold text-claude-text text-sm mb-3">Statistics</h4>
                  <div className="space-y-1.5 text-sm text-claude-text-secondary font-mono">
                    <div className="flex justify-between">
                      <span>Total documents</span>
                      <span className="text-claude-text font-medium">{digest.stats.total_docs}</span>
                    </div>
                    {digest.stats.date_range && (
                      <div className="flex justify-between">
                        <span>Date range</span>
                        <span className="text-claude-text">{digest.stats.date_range}</span>
                      </div>
                    )}
                    {digest.stats.top_authors?.length > 0 && (
                      <div className="pt-2">
                        <p className="text-claude-text-tertiary mb-1.5">Top contributors</p>
                        <div className="flex flex-wrap gap-1.5">
                          {digest.stats.top_authors.slice(0, 5).map((a, i) => (
                            <span key={i} className="px-2 py-0.5 bg-white border border-claude-border rounded text-xs">
                              {a.name} ({a.count})
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={() => { navigator.clipboard.writeText(JSON.stringify(digest, null, 2)); alert('Copied!') }}
                  className="flex-1 px-4 py-2.5 bg-claude-code-bg hover:bg-claude-border text-claude-text rounded-xl text-sm font-semibold transition-colors">
                  Copy JSON
                </button>
                <button
                  onClick={onClose}
                  className="px-6 py-2.5 text-white rounded-xl text-sm font-semibold transition-all hover:-translate-y-0.5"
                  style={{ background: 'linear-gradient(135deg, #D97757, #C4673F)' }}>
                  Close
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-claude-text-secondary text-sm">Failed to generate digest</div>
          )}
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
