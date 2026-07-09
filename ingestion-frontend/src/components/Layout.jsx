import { useState, useEffect } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'

export default function Layout() {
  const location = useLocation()
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const navLinks = [
    { to: '/',        label: 'Home' },
    { to: '/sources', label: 'Sources' },
    { to: '/chat',    label: 'Chat' },
    { to: '/graph',   label: 'Graph' },
  ]

  const isActive = (path) =>
    path === '/' ? location.pathname === '/' : location.pathname.startsWith(path)

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Header ──────────────────────────────────────────── */}
      <header
        className="sticky top-0 z-50 transition-all duration-300"
        style={{
          background: scrolled ? 'rgba(255,255,255,0.85)' : 'rgba(247,246,243,0.95)',
          backdropFilter: scrolled ? 'blur(12px)' : 'none',
          borderBottom: '1px solid #E8E6E0',
          boxShadow: scrolled ? '0 1px 12px rgba(0,0,0,0.06)' : 'none',
        }}>
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3 group">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-claude"
                style={{ background: 'linear-gradient(135deg, #D97757, #C4673F)' }}>
                N
              </div>
              <span className="font-display text-2xl font-bold text-claude-text">Niyanta</span>
            </Link>

            {/* Nav */}
            <nav className="flex items-center gap-1">
              {navLinks.map(({ to, label }) => {
                const active = isActive(to)
                return (
                  <Link key={to} to={to}
                    className="relative px-4 py-2 rounded-lg text-sm font-semibold transition-colors"
                    style={{ color: active ? '#D97757' : '#5C5C5C' }}>
                    {label}
                    {/* Animated underline */}
                    <span
                      className="absolute bottom-1 left-4 right-4 h-0.5 rounded-full transition-all duration-300"
                      style={{
                        background: '#D97757',
                        width: active ? 'calc(100% - 2rem)' : '0',
                        opacity: active ? 1 : 0,
                      }} />
                  </Link>
                )
              })}
            </nav>

            {/* Right badge */}
            <div className="hidden md:flex items-center gap-2 text-xs font-mono text-claude-text-tertiary">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              Knowledge Q&A
            </div>
          </div>
        </div>
      </header>

      {/* ── Main ────────────────────────────────────────────── */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* ── Footer ──────────────────────────────────────────── */}
      <footer className="bg-white border-t border-claude-border">
        <div className="max-w-7xl mx-auto px-6 py-5">
          <div className="flex items-center justify-between text-sm text-claude-text-tertiary">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-lg flex items-center justify-center text-white text-xs font-bold"
                style={{ background: '#D97757' }}>N</div>
              <span className="font-mono">Niyanta</span>
            </div>
            <div className="font-mono text-xs">Powered by Agentic RAG · © 2026</div>
          </div>
        </div>
      </footer>
    </div>
  )
}
