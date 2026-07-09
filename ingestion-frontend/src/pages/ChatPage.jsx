import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import SourceFilter from '../components/SourceFilter'

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sourceFilter, setSourceFilter] = useState(null)
  const endRef = useRef(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMsg = { id: Date.now(), role: 'user', content: input, timestamp: new Date().toISOString() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const r = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input, use_cache: true, force_agentic: false, source_filter: sourceFilter }),
      })
      if (!r.ok) throw new Error('Failed to get response')
      const data = await r.json()
      setMessages(prev => [...prev, {
        id: Date.now() + 1, role: 'assistant',
        content: data.answer, sources: data.sources || [],
        metadata: data.metadata || {}, confidence: data.confidence,
        pipeline: data.pipeline, cache_hit: data.cache_hit,
        processing_time_ms: data.processing_time_ms,
        timestamp: new Date().toISOString(),
      }])
    } catch {
      setMessages(prev => [...prev, {
        id: Date.now() + 1, role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        error: true, timestamp: new Date().toISOString(),
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col max-w-4xl mx-auto">
      {/* Header */}
      <div className="px-6 py-4 border-b border-claude-border bg-claude-surface">
        <div className="flex items-center justify-between mb-3">
          <h1 className="font-display text-3xl font-bold text-claude-text">Chat</h1>
          <button
            onClick={() => { if (confirm('Clear all messages?')) setMessages([]) }}
            className="text-xs font-mono text-claude-text-tertiary hover:text-claude-text transition-colors px-3 py-1.5 rounded-lg hover:bg-claude-code-bg">
            Clear
          </button>
        </div>
        <SourceFilter selectedSource={sourceFilter} onSourceChange={setSourceFilter} />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto custom-scrollbar px-6 py-6 bg-claude-bg">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-sm">
              <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-5"
                style={{ background: 'linear-gradient(135deg, #FDF1EC, #F5E0D5)' }}>
                <svg className="w-8 h-8" style={{ color: '#D97757' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h3 className="font-display text-2xl font-bold text-claude-text mb-2">Start a Conversation</h3>
              <p className="text-claude-text-secondary text-sm leading-relaxed">
                Ask questions about your ingested sources. Answers come with citations.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-5">
            {messages.map(msg => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'user' ? (
                  /* User bubble — terracotta tint, right-aligned */
                  <div className="max-w-2xl px-5 py-3.5 rounded-2xl rounded-tr-sm text-claude-text text-sm leading-relaxed animate-slideRight"
                    style={{ background: '#FDF1EC', border: '1px solid #EDD5C8' }}>
                    {msg.content}
                  </div>
                ) : (
                  /* Assistant card — white, left border accent */
                  <div className="max-w-3xl w-full animate-fadeIn">
                    <div className={`rounded-2xl rounded-tl-sm overflow-hidden shadow-claude ${msg.error ? 'border border-red-200' : 'border border-claude-border bg-claude-surface'}`}>
                      {/* Terracotta left stripe */}
                      {!msg.error && (
                        <div className="flex">
                          <div className="w-1 flex-shrink-0" style={{ background: 'linear-gradient(180deg, #D97757, #C4673F)' }} />
                          <div className="flex-1 p-5">
                            <div className="markdown-content text-sm">
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                            </div>

                            {/* Meta row */}
                            {msg.metadata && (
                              <div className="mt-4 pt-3 border-t border-claude-border flex flex-wrap gap-3">
                                {[
                                  msg.pipeline && ['Pipeline', msg.pipeline],
                                  msg.confidence !== undefined && ['Confidence', `${(msg.confidence * 100).toFixed(0)}%`],
                                  msg.cache_hit !== undefined && ['Cache', msg.cache_hit ? 'Hit' : 'Miss'],
                                  msg.processing_time_ms && ['Time', `${msg.processing_time_ms.toFixed(0)}ms`],
                                ].filter(Boolean).map(([k, v]) => (
                                  <span key={k} className="text-xs font-mono text-claude-text-tertiary">
                                    <span className="text-claude-text-secondary">{k}:</span> {v}
                                  </span>
                                ))}
                              </div>
                            )}

                            {/* Sources */}
                            {msg.sources?.length > 0 && (
                              <div className="mt-4 pt-3 border-t border-claude-border">
                                <p className="text-xs font-semibold text-claude-text mb-2">
                                  Sources ({msg.sources.length})
                                </p>
                                <div className="space-y-2">
                                  {msg.sources.slice(0, 5).map((src, i) => (
                                    <div key={i} className="bg-claude-code-bg rounded-xl p-3 text-xs">
                                      {src.source_url && src.source_id && (
                                        <a href={src.source_url} target="_blank" rel="noopener noreferrer"
                                          className="font-semibold mb-1 block" style={{ color: '#D97757' }}>
                                          {src.source_id}
                                        </a>
                                      )}
                                      <p className="text-claude-text-secondary line-clamp-2">{src.content}</p>
                                      {src.source_type && (
                                        <span className="mt-1.5 inline-block px-2 py-0.5 bg-white border border-claude-border rounded font-mono text-claude-text-tertiary">
                                          {src.source_type}
                                        </span>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {msg.error && (
                        <div className="p-5 text-sm text-red-700">{msg.content}</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Loading dots */}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-claude-surface border border-claude-border rounded-2xl rounded-tl-sm px-5 py-4 shadow-claude">
                  <div className="flex items-center gap-1.5">
                    {[0, 150, 300].map(delay => (
                      <div key={delay} className="w-2 h-2 rounded-full"
                        style={{ background: '#D97757', animation: `bounceDot 1.2s ease-in-out ${delay}ms infinite` }} />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>
        )}
      </div>

      {/* Input bar */}
      <div className="px-6 py-4 border-t border-claude-border bg-claude-surface">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask a question about your sources…"
            disabled={loading}
            className="flex-1 px-5 py-3 bg-claude-bg border border-claude-border rounded-full text-claude-text placeholder-claude-text-tertiary text-sm focus:outline-none transition-all disabled:opacity-50"
            style={{ '--tw-ring-color': '#D97757' }}
            onFocus={e => e.target.style.boxShadow = '0 0 0 2px #D9775740'}
            onBlur={e => e.target.style.boxShadow = 'none'}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-6 py-3 text-white rounded-full font-semibold text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:-translate-y-0.5 hover:shadow-claude-lg"
            style={{ background: 'linear-gradient(135deg, #D97757, #C4673F)' }}>
            Send
          </button>
        </form>
      </div>
    </div>
  )
}
