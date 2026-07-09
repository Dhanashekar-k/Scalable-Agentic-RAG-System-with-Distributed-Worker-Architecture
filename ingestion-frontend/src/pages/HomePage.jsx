import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'

/* ── SVG source icons ─────────────────────────────────────── */
const GithubIcon = ({ className }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24">
    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
  </svg>
)
const WebIcon = ({ className }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
  </svg>
)
const PdfIcon = ({ className }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
  </svg>
)
const YoutubeIcon = ({ className }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24">
    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
  </svg>
)
const RedditIcon = ({ className }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24">
    <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
  </svg>
)
const RssIcon = ({ className }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24">
    <path d="M6.503 20.752c0 1.794-1.456 3.248-3.251 3.248-1.796 0-3.252-1.454-3.252-3.248 0-1.794 1.456-3.248 3.252-3.248 1.795.001 3.251 1.454 3.251 3.248zm-6.503-12.572v4.811c6.05.062 10.96 4.966 11.022 11.009h4.817c-.062-8.71-7.118-15.758-15.839-15.82zm0-3.368c10.58.046 19.152 8.594 19.183 19.188h4.817c-.03-13.231-10.755-23.954-24-24v4.812z"/>
  </svg>
)

/* ── Floating icon config ─────────────────────────────────── */
const FLOATING_ICONS = [
  { Icon: GithubIcon,  label: 'GitHub',   delay: '0s',    top: '18%', left: '8%',   color: '#1A1A1A' },
  { Icon: WebIcon,     label: 'Web',      delay: '0.6s',  top: '12%', right: '10%', color: '#2196F3' },
  { Icon: PdfIcon,     label: 'PDF',      delay: '1.2s',  top: '55%', left: '5%',   color: '#EF4444' },
  { Icon: YoutubeIcon, label: 'YouTube',  delay: '0.3s',  top: '65%', right: '7%',  color: '#FF0000' },
  { Icon: RedditIcon,  label: 'Reddit',   delay: '0.9s',  top: '30%', right: '4%',  color: '#FF4500' },
  { Icon: RssIcon,     label: 'RSS',      delay: '1.5s',  top: '40%', left: '3%',   color: '#F97316' },
]

/* ── Scroll-reveal hook ───────────────────────────────────── */
function useScrollReveal() {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect() } },
      { threshold: 0.15 }
    )
    if (ref.current) obs.observe(ref.current)
    return () => obs.disconnect()
  }, [])
  return [ref, visible]
}

export default function HomePage() {
  /* Hero word-by-word reveal */
  const words = ['Transform', 'Any', 'Source', 'Into', 'Searchable', 'Knowledge']
  const [visibleWords, setVisibleWords] = useState(0)
  useEffect(() => {
    let i = 0
    const t = setInterval(() => {
      i++
      setVisibleWords(i)
      if (i >= words.length) clearInterval(t)
    }, 120)
    return () => clearInterval(t)
  }, [])

  const [statsRef, statsVisible] = useScrollReveal()
  const [featRef,  featVisible]  = useScrollReveal()
  const [stepsRef, stepsVisible] = useScrollReveal()
  const [srcRef,   srcVisible]   = useScrollReveal()

  return (
    <div className="min-h-screen overflow-x-hidden">

      {/* ── Hero ──────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex items-center overflow-hidden"
        style={{ background: 'linear-gradient(135deg, #F7F6F3 0%, #FDFCFA 40%, #F5F0EB 100%)' }}>

        {/* Animated gradient orbs */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute w-[600px] h-[600px] rounded-full opacity-20"
            style={{ background: 'radial-gradient(circle, #D97757 0%, transparent 70%)', top: '-10%', right: '-5%',
              animation: 'float 8s ease-in-out infinite' }} />
          <div className="absolute w-[400px] h-[400px] rounded-full opacity-10"
            style={{ background: 'radial-gradient(circle, #D97757 0%, transparent 70%)', bottom: '5%', left: '-5%',
              animation: 'float 6s ease-in-out infinite', animationDelay: '2s' }} />
        </div>

        {/* Floating source icons */}
        {FLOATING_ICONS.map(({ Icon, label, delay, top, left, right, color }) => (
          <div key={label}
            className="absolute hidden lg:flex flex-col items-center gap-1.5 animate-float"
            style={{ top, left, right, animationDelay: delay }}>
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center shadow-claude-lg"
              style={{ background: 'rgba(255,255,255,0.7)', backdropFilter: 'blur(8px)',
                border: '1px solid rgba(255,255,255,0.9)' }}>
              <Icon className="w-6 h-6" style={{ color }} />
            </div>
            <span className="text-xs font-mono text-claude-text-tertiary">{label}</span>
          </div>
        ))}

        {/* Hero content */}
        <div className="relative max-w-5xl mx-auto px-6 py-24 text-center w-full">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-white/80 border border-claude-border rounded-full text-xs font-mono text-claude-text-secondary mb-8 shadow-claude">
            <span className="w-1.5 h-1.5 rounded-full bg-claude-accent animate-pulse" />
            Agentic RAG · Hybrid Search · Knowledge Graphs
          </div>

          <h1 className="font-display text-6xl md:text-7xl lg:text-8xl font-black text-claude-text leading-[1.05] mb-6">
            {words.map((word, i) => (
              <span key={word}
                className="inline-block mr-[0.2em] transition-all duration-500"
                style={{
                  opacity: i < visibleWords ? 1 : 0,
                  transform: i < visibleWords ? 'translateY(0)' : 'translateY(16px)',
                  color: word === 'Knowledge' ? '#D97757' : undefined,
                }}>
                {word}
              </span>
            ))}
          </h1>

          <p className="text-xl text-claude-text-secondary max-w-2xl mx-auto mb-10 leading-relaxed animate-fadeUp"
            style={{ animationDelay: '0.8s', opacity: 0, animationFillMode: 'forwards' }}>
            Ingest GitHub repos, webpages, PDFs, YouTube, Reddit, and RSS feeds.
            Ask questions and get precise answers with citations.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fadeUp"
            style={{ animationDelay: '1s', opacity: 0, animationFillMode: 'forwards' }}>
            <Link to="/sources"
              className="group px-8 py-4 bg-claude-accent hover:bg-claude-accent-hover text-white rounded-xl font-semibold text-lg transition-all shadow-claude-lg hover:shadow-claude-xl hover:-translate-y-0.5">
              Get Started
              <span className="ml-2 inline-block transition-transform group-hover:translate-x-1">→</span>
            </Link>
            <Link to="/chat"
              className="px-8 py-4 bg-white/80 hover:bg-white text-claude-text border border-claude-border rounded-xl font-semibold text-lg transition-all shadow-claude hover:shadow-claude-lg backdrop-blur-sm">
              Try the Chat
            </Link>
          </div>
        </div>
      </section>

      {/* ── Stats bar ─────────────────────────────────────────── */}
      <div ref={statsRef}
        className="bg-white border-y border-claude-border py-5 transition-all duration-700"
        style={{ opacity: statsVisible ? 1 : 0, transform: statsVisible ? 'none' : 'translateY(12px)' }}>
        <div className="max-w-5xl mx-auto px-6">
          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm font-mono text-claude-text-secondary">
            {['6 Source Types', 'Real-time Ingestion', 'Cited Answers', 'Knowledge Graphs', 'Hybrid Search'].map((stat, i) => (
              <span key={stat} className="flex items-center gap-3">
                {i > 0 && <span className="text-claude-accent font-bold">·</span>}
                {stat}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* ── Features ──────────────────────────────────────────── */}
      <section className="py-24 bg-white" ref={featRef}>
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="font-display text-5xl md:text-6xl font-bold text-claude-text mb-4">
              Everything You Need
            </h2>
            <p className="text-lg text-claude-text-secondary max-w-xl mx-auto">
              A complete platform for knowledge ingestion, organization, and retrieval
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: (
                  <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                ),
                title: 'Universal Ingestion',
                body: 'GitHub repos, docs, PDFs, YouTube, Reddit, RSS — one platform for all your knowledge sources.',
                link: '/sources', cta: 'Add a source',
              },
              {
                icon: (
                  <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                ),
                title: 'Cited Answers',
                body: 'Every answer links back to the exact source — issue numbers, page refs, timestamps.',
                link: '/chat', cta: 'Try it now',
              },
              {
                icon: (
                  <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                ),
                title: 'Smart Digests',
                body: 'Auto-summarize what happened in your sources — issues, PRs, commits, discussions.',
                link: '/sources', cta: 'See example',
              },
            ].map(({ icon, title, body, link, cta }, i) => (
              <div key={title}
                className="bg-claude-surface border border-claude-border rounded-2xl p-8 shadow-claude hover:shadow-claude-xl hover:-translate-y-1 transition-all duration-300 flex flex-col"
                style={{
                  opacity: featVisible ? 1 : 0,
                  transform: featVisible ? 'none' : 'translateY(24px)',
                  transition: `opacity 0.6s ease ${i * 0.12}s, transform 0.6s ease ${i * 0.12}s, box-shadow 0.2s, translate 0.2s`,
                }}>
                <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6"
                  style={{ background: 'linear-gradient(135deg, #D97757, #C4673F)' }}>
                  {icon}
                </div>
                <h3 className="font-display text-2xl font-bold text-claude-text mb-3">{title}</h3>
                <p className="text-claude-text-secondary leading-relaxed flex-1">{body}</p>
                <Link to={link}
                  className="mt-5 inline-flex items-center gap-1 text-sm font-semibold text-claude-accent hover:text-claude-accent-hover transition-colors">
                  {cta}
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ──────────────────────────────────────── */}
      <section className="py-24 bg-claude-bg" ref={stepsRef}>
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="font-display text-5xl md:text-6xl font-bold text-claude-text mb-4">
              How It Works
            </h2>
            <p className="text-lg text-claude-text-secondary">Three steps to searchable knowledge</p>
          </div>

          <div className="relative grid md:grid-cols-3 gap-12">
            {/* Connecting line */}
            <div className="hidden md:block absolute top-8 left-[calc(16.67%+1rem)] right-[calc(16.67%+1rem)] h-px bg-claude-border" />

            {[
              { n: '01', title: 'Add Your Source', body: 'Paste a URL or upload a PDF. We detect the type and start processing immediately.' },
              { n: '02', title: 'Watch It Process', body: 'Real-time progress as we extract, chunk, embed, and index your content.' },
              { n: '03', title: 'Ask Questions', body: 'Get instant cited answers. Filter by source, generate digests, explore the graph.' },
            ].map(({ n, title, body }, i) => (
              <div key={n} className="text-center relative"
                style={{
                  opacity: stepsVisible ? 1 : 0,
                  transform: stepsVisible ? 'none' : 'translateY(20px)',
                  transition: `opacity 0.6s ease ${i * 0.18}s, transform 0.6s ease ${i * 0.18}s`,
                }}>
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white border-2 border-claude-border mb-6 relative z-10">
                  <span className="font-display text-2xl font-black text-claude-accent">{n}</span>
                </div>
                <h3 className="font-display text-2xl font-bold text-claude-text mb-3">{title}</h3>
                <p className="text-claude-text-secondary leading-relaxed">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Source grid ───────────────────────────────────────── */}
      <section className="py-24 bg-white" ref={srcRef}>
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2 className="font-display text-5xl md:text-6xl font-bold text-claude-text mb-4">
              Supported Sources
            </h2>
            <p className="text-lg text-claude-text-secondary">Ingest from your favourite platforms</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              { Icon: GithubIcon,  label: 'GitHub',    color: '#1A1A1A' },
              { Icon: WebIcon,     label: 'Webpages',  color: '#2196F3' },
              { Icon: PdfIcon,     label: 'PDFs',      color: '#EF4444' },
              { Icon: YoutubeIcon, label: 'YouTube',   color: '#FF0000' },
              { Icon: RedditIcon,  label: 'Reddit',    color: '#FF4500' },
              { Icon: RssIcon,     label: 'RSS Feeds', color: '#F97316' },
            ].map(({ Icon, label, color }, i) => (
              <div key={label}
                className="group bg-claude-surface border border-claude-border rounded-2xl p-6 text-center hover:shadow-claude-lg hover:-translate-y-1 transition-all duration-200 cursor-default"
                style={{
                  opacity: srcVisible ? 1 : 0,
                  transform: srcVisible ? 'none' : 'translateY(16px)',
                  transition: `opacity 0.5s ease ${i * 0.07}s, transform 0.5s ease ${i * 0.07}s, box-shadow 0.2s, translate 0.2s`,
                }}>
                <div className="w-12 h-12 mx-auto mb-3 rounded-xl flex items-center justify-center transition-colors"
                  style={{ background: `${color}15` }}>
                  <Icon className="w-6 h-6 transition-colors" style={{ color }} />
                </div>
                <div className="text-sm font-semibold text-claude-text">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────── */}
      <section className="py-24 relative overflow-hidden" style={{ background: '#1A1A1A' }}>
        {/* Grain texture */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none"
          style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
            backgroundSize: '200px 200px' }} />
        {/* Accent glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] opacity-20 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, #D97757 0%, transparent 70%)' }} />

        <div className="relative max-w-3xl mx-auto px-6 text-center">
          <h2 className="font-display text-5xl md:text-6xl font-black text-white mb-6 leading-tight">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-white/70 mb-10 leading-relaxed">
            Transform your content into searchable knowledge in minutes
          </p>
          <Link to="/sources"
            className="inline-block px-10 py-4 bg-claude-accent hover:bg-claude-accent-hover text-white rounded-xl font-semibold text-lg transition-all shadow-claude-xl hover:-translate-y-0.5">
            Add Your First Source
          </Link>
        </div>
      </section>
    </div>
  )
}
