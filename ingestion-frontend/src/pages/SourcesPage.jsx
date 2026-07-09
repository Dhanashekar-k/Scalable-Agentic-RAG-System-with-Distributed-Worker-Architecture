import { useState, useEffect } from 'react'
import SourceCard from '../components/SourceCard'
import DigestModal from '../components/DigestModal'

export default function SourcesPage() {
  const [url, setUrl] = useState('')
  const [recursive, setRecursive] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sources, setSources] = useState([])
  const [digestModal, setDigestModal] = useState(null)

  useEffect(() => {
    fetchSources()
    const interval = setInterval(fetchSources, 3000)
    return () => clearInterval(interval)
  }, [])

  const fetchSources = async () => {
    try {
      const r = await fetch('/api/ingest/list')
      if (r.ok) {
        const data = await r.json()
        setSources(data.ingestions)
      }
    } catch {}
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!url.trim()) return
    setLoading(true)
    setError(null)
    try {
      const r = await fetch('/api/ingest/url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, recursive }),
      })
      if (!r.ok) throw new Error('Failed to start ingestion')
      setUrl('')
      setRecursive(false)
      fetchSources()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const r = await fetch('/api/ingest/pdf', { method: 'POST', body: fd })
      if (!r.ok) throw new Error('Failed to upload PDF')
      fetchSources()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
      e.target.value = ''
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this source?')) return
    try {
      const r = await fetch(`/api/ingest/${id}`, { method: 'DELETE' })
      if (r.ok) fetchSources()
    } catch {}
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      {/* Page title */}
      <div className="mb-10">
        <h1 className="font-display text-5xl font-bold text-claude-text mb-2">Manage Sources</h1>
        <p className="text-claude-text-secondary">Add new sources or manage existing ones</p>
      </div>

      {/* Ingest form */}
      <div className="bg-claude-surface border border-claude-border rounded-2xl shadow-claude mb-10 overflow-hidden">
        {/* Left accent bar */}
        <div className="flex">
          <div className="w-1 flex-shrink-0 rounded-l-2xl" style={{ background: 'linear-gradient(180deg, #D97757, #C4673F)' }} />
          <div className="flex-1 p-8">
            <h2 className="font-display text-2xl font-bold text-claude-text mb-6">Add New Source</h2>

            {error && (
              <div className="mb-5 px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="mb-6">
              <label className="block text-sm font-semibold text-claude-text mb-2">URL</label>
              <div className="flex gap-3">
                <input
                  type="url"
                  value={url}
                  onChange={e => setUrl(e.target.value)}
                  placeholder="https://github.com/expressjs/express"
                  disabled={loading}
                  className="flex-1 px-4 py-3 bg-claude-bg border border-claude-border rounded-xl text-claude-text placeholder-claude-text-tertiary focus:outline-none focus:ring-2 focus:border-transparent transition-all"
                  style={{ '--tw-ring-color': '#D97757' }}
                />
                <button
                  type="submit"
                  disabled={loading || !url.trim()}
                  className="px-6 py-3 text-white rounded-xl font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:-translate-y-0.5 hover:shadow-claude-lg"
                  style={{ background: loading || !url.trim() ? '#D97757' : 'linear-gradient(135deg, #D97757, #C4673F)' }}>
                  {loading ? 'Starting…' : 'Ingest'}
                </button>
              </div>
              <p className="mt-2 text-xs text-claude-text-tertiary font-mono">
                GitHub · Webpages · YouTube · Reddit · RSS
              </p>

              <label className="mt-4 flex items-center gap-2 cursor-pointer w-fit">
                <input
                  type="checkbox"
                  checked={recursive}
                  onChange={e => setRecursive(e.target.checked)}
                  className="w-4 h-4 rounded accent-[#D97757]"
                />
                <span className="text-sm text-claude-text-secondary">Recursive crawl (docs sites, max 20 pages)</span>
              </label>
            </form>

            <div className="border-t border-claude-border pt-6">
              <label className="block text-sm font-semibold text-claude-text mb-2">Or upload a PDF</label>
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                disabled={loading}
                className="text-sm text-claude-text-secondary
                  file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border file:border-claude-border
                  file:text-sm file:font-semibold file:bg-claude-code-bg file:text-claude-text
                  hover:file:bg-claude-border file:cursor-pointer file:transition-colors
                  disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Sources list */}
      <div>
        <h2 className="font-display text-2xl font-bold text-claude-text mb-5">
          Your Sources
          <span className="ml-2 text-base font-mono font-normal text-claude-text-tertiary">({sources.length})</span>
        </h2>

        {sources.length === 0 ? (
          <div className="bg-claude-surface border border-claude-border rounded-2xl p-16 text-center shadow-claude">
            <div className="w-16 h-16 bg-claude-code-bg rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-claude-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <p className="text-claude-text-secondary">No sources yet. Add your first source above.</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {sources.map(source => (
              <SourceCard
                key={source.ingestion_id}
                source={source}
                onDelete={handleDelete}
                onDigest={id => setDigestModal(id)}
              />
            ))}
          </div>
        )}
      </div>

      {digestModal && (
        <DigestModal ingestionId={digestModal} onClose={() => setDigestModal(null)} />
      )}
    </div>
  )
}
