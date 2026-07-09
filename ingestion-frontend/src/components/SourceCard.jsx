import { useState } from 'react'
import { Link } from 'react-router-dom'
import MiniGraph from './MiniGraph'

const TYPE_ICONS = {
  github_repo: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
    </svg>
  ),
  webpage: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
    </svg>
  ),
  pdf: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>
  ),
  youtube: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
    </svg>
  ),
  reddit: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
    </svg>
  ),
  rss: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M6.503 20.752c0 1.794-1.456 3.248-3.251 3.248-1.796 0-3.252-1.454-3.252-3.248 0-1.794 1.456-3.248 3.252-3.248 1.795.001 3.251 1.454 3.251 3.248zm-6.503-12.572v4.811c6.05.062 10.96 4.966 11.022 11.009h4.817c-.062-8.71-7.118-15.758-15.839-15.82zm0-3.368c10.58.046 19.152 8.594 19.183 19.188h4.817c-.03-13.231-10.755-23.954-24-24v4.812z"/>
    </svg>
  ),
}

export default function SourceCard({ source, onDelete, onDigest }) {
  const [showGraph, setShowGraph] = useState(false)

  const icon = TYPE_ICONS[source.source_type] || TYPE_ICONS.webpage

  const statusBadge = () => {
    if (source.status === 'running') return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium border"
        style={{ background: '#EFF6FF', borderColor: '#BFDBFE', color: '#1D4ED8' }}>
        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
        Running
      </span>
    )
    if (source.status === 'complete') return (
      <span className="px-3 py-1 rounded-full text-xs font-mono font-medium border"
        style={{ background: '#F0FDF4', borderColor: '#BBF7D0', color: '#15803D' }}>
        Complete
      </span>
    )
    if (source.status === 'failed') return (
      <span className="px-3 py-1 rounded-full text-xs font-mono font-medium border"
        style={{ background: '#FEF2F2', borderColor: '#FECACA', color: '#DC2626' }}>
        Failed
      </span>
    )
  }

  return (
    <div className="bg-claude-surface border border-claude-border rounded-2xl shadow-claude hover:shadow-claude-lg transition-all duration-200 overflow-hidden">
      {/* Running shimmer */}
      {source.status === 'running' && (
        <div className="h-0.5 shimmer-bg" />
      )}

      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-4 flex-1 min-w-0">
            <div className="flex-shrink-0 w-11 h-11 rounded-xl flex items-center justify-center"
              style={{ background: '#FDF1EC', color: '#D97757' }}>
              {icon}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-claude-text mb-0.5 truncate">{source.source_name}</h3>
              <p className="text-xs text-claude-text-tertiary font-mono truncate">{source.source_url}</p>
            </div>
          </div>
          <div className="flex-shrink-0 ml-4">{statusBadge()}</div>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-3 mb-3 text-xs font-mono text-claude-text-tertiary">
          <span>{source.total_docs} docs</span>
          <span className="text-claude-accent">·</span>
          <span>{source.entity_count} entities</span>
          <span className="text-claude-accent">·</span>
          <span>{new Date(source.created_at).toLocaleDateString()}</span>
        </div>

        {source.message && (
          <p className="text-xs text-claude-text-secondary mb-4 line-clamp-1">{source.message}</p>
        )}

        {source.status === 'complete' && (
          <div>
            <div className="flex flex-wrap gap-2">
              <Link to="/chat"
                className="px-4 py-2 text-white rounded-lg text-sm font-semibold transition-all hover:-translate-y-0.5 hover:shadow-claude"
                style={{ background: 'linear-gradient(135deg, #D97757, #C4673F)' }}>
                Ask Questions
              </Link>
              <button
                onClick={() => onDigest(source.ingestion_id)}
                className="px-4 py-2 bg-claude-code-bg hover:bg-claude-border text-claude-text rounded-lg text-sm font-semibold transition-colors">
                Generate Digest
              </button>
              <button
                onClick={() => onDelete(source.ingestion_id)}
                className="px-4 py-2 rounded-lg text-sm font-semibold transition-colors border"
                style={{ background: '#FEF2F2', borderColor: '#FECACA', color: '#DC2626' }}>
                Delete
              </button>
            </div>

            {source.entity_count > 0 && (
              <div className="mt-4">
                <button
                  onClick={() => setShowGraph(p => !p)}
                  className="text-xs font-semibold transition-colors"
                  style={{ color: '#D97757' }}>
                  {showGraph ? '▾ Hide knowledge graph' : '▸ Show knowledge graph'}
                </button>
                {showGraph && (
                  <div className="mt-2 h-56 rounded-xl border border-claude-border overflow-hidden">
                    <MiniGraph ingestionId={source.ingestion_id} />
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
