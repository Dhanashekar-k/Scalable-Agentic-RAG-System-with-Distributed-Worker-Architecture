import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import MiniGraph from '../components/MiniGraph';

function IngestionPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [url, setUrl] = useState('');
  const [recursive, setRecursive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [ingestions, setIngestions] = useState([]);
  const [error, setError] = useState(null);
  const [digestModal, setDigestModal] = useState(null);
  const [digest, setDigest] = useState(null);
  const [digestLoading, setDigestLoading] = useState(false);
  const [expandedGraph, setExpandedGraph] = useState(null);

  useEffect(() => {
    fetchIngestions();
    const interval = setInterval(() => {
      fetchIngestions();
    }, 3000); // Poll every 3 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchIngestions = async () => {
    try {
      const response = await fetch('/api/ingest/list');
      if (response.ok) {
        const data = await response.json();
        setIngestions(data.ingestions);
      }
    } catch (error) {
      console.error('Failed to fetch ingestions:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/ingest/url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, recursive }),
      });

      if (!response.ok) {
        throw new Error('Failed to start ingestion');
      }

      const data = await response.json();
      setUrl('');
      fetchIngestions();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/ingest/pdf', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload PDF');
      }

      fetchIngestions();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (ingestionId) => {
    if (!confirm('Are you sure you want to delete this ingestion?')) return;

    try {
      const response = await fetch(`/api/ingest/${ingestionId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchIngestions();
      }
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  };

  const handleGenerateDigest = async (ingestionId, daysBack = 7) => {
    setDigestLoading(true);
    setDigest(null);

    try {
      const response = await fetch('/api/digest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ingestion_id: ingestionId, days_back: daysBack }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate digest');
      }

      const data = await response.json();
      setDigest(data);
    } catch (error) {
      console.error('Failed to generate digest:', error);
      alert('Failed to generate digest');
    } finally {
      setDigestLoading(false);
    }
  };

  const getTypeIcon = (type) => {
    const icons = {
      github_repo: '🐙',
      webpage: '🌐',
      pdf: '📄',
      youtube: '🎥',
      reddit: '💬',
      rss: '📡',
    };
    return icons[type] || '📄';
  };

  return (
    <div className="flex h-screen bg-black text-white">
      {/* Left Sidebar */}
      <aside className="w-80 border-r border-gray-800 flex flex-col">
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-center gap-3 mb-1">
            <div className="text-2xl font-bold">NIYANTA</div>
          </div>
          <div className="text-xs text-gray-500 uppercase tracking-wider">
            Ingestion Manager
          </div>
        </div>

        <div className="px-6 py-4 border-b border-gray-800 bg-gray-900/30">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">
            Current User
          </div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-white">
                {user?.username || 'Guest'}
              </div>
              <div className="text-xs text-gray-600 font-mono">
                {user?.id?.slice(0, 12)}...
              </div>
            </div>
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="w-full py-2 px-3 bg-gray-900 hover:bg-gray-800 border border-gray-800 rounded text-sm text-gray-400 hover:text-white transition-colors"
            >
              ← Back to Dashboard
            </button>
          </div>
        </div>

        <div className="p-4 border-t border-gray-800 space-y-3">
          <button
            onClick={() => {
              logout();
              navigate('/');
            }}
            className="w-full py-2 px-3 bg-gray-900 hover:bg-gray-800 border border-gray-800 rounded text-sm text-gray-400 hover:text-white transition-colors"
          >
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="px-8 py-6 border-b border-gray-800">
          <h1 className="text-3xl font-bold mb-2">Manage Sources</h1>
          <p className="text-gray-500">
            Ingest GitHub repos, webpages, PDFs, and more
          </p>
        </header>

        <div className="flex-1 overflow-y-auto p-8">
          <div className="max-w-6xl mx-auto">
            {/* Add New Source */}
            <div className="mb-8 bg-gray-950 border border-gray-800 rounded p-6">
              <h2 className="text-xl font-bold mb-4">Add New Source</h2>

              {error && (
                <div className="mb-4 p-3 bg-red-950/50 border border-red-900 rounded text-red-400 text-sm">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="mb-6">
                <div className="mb-4">
                  <label className="block text-sm text-gray-500 mb-2">
                    URL (GitHub, webpage, YouTube, Reddit, RSS)
                  </label>
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://github.com/expressjs/express"
                    className="w-full px-4 py-2 bg-gray-900 border border-gray-800 rounded text-white placeholder-gray-700 focus:outline-none focus:border-gray-700"
                    disabled={loading}
                  />
                </div>

                <div className="mb-4 flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="recursive"
                    checked={recursive}
                    onChange={(e) => setRecursive(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <label htmlFor="recursive" className="text-sm text-gray-400">
                    Recursive crawl (for documentation sites)
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={loading || !url.trim()}
                  className="px-6 py-2 bg-white text-black text-sm font-medium rounded hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-all uppercase tracking-wider"
                >
                  {loading ? 'Starting...' : 'Detect & Ingest'}
                </button>
              </form>

              <div className="border-t border-gray-800 pt-6">
                <label className="block text-sm text-gray-500 mb-2">
                  Or upload a PDF
                </label>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  disabled={loading}
                  className="text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-gray-900 file:text-gray-300 hover:file:bg-gray-800 file:cursor-pointer"
                />
              </div>
            </div>

            {/* Your Sources */}
            <div>
              <h2 className="text-xl font-bold mb-4">Your Sources</h2>

              {ingestions.length === 0 ? (
                <div className="text-center py-12 text-gray-600">
                  <p>No sources ingested yet</p>
                </div>
              ) : (
                <div className="grid gap-4">
                  {ingestions.map((ing) => (
                    <div
                      key={ing.ingestion_id}
                      className="bg-gray-950 border border-gray-800 rounded p-6"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-start gap-3">
                          <div className="text-2xl">
                            {getTypeIcon(ing.source_type)}
                          </div>
                          <div>
                            <h3 className="font-medium text-white mb-1">
                              {ing.source_name}
                            </h3>
                            <p className="text-sm text-gray-500 break-all">
                              {ing.source_url}
                            </p>
                          </div>
                        </div>

                        <div>
                          {ing.status === 'running' && (
                            <span className="inline-flex items-center gap-2 px-3 py-1 bg-blue-950/50 border border-blue-900 rounded text-blue-400 text-xs">
                              <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                              Running
                            </span>
                          )}
                          {ing.status === 'complete' && (
                            <span className="px-3 py-1 bg-green-950/50 border border-green-900 rounded text-green-400 text-xs">
                              Complete
                            </span>
                          )}
                          {ing.status === 'failed' && (
                            <span className="px-3 py-1 bg-red-950/50 border border-red-900 rounded text-red-400 text-xs">
                              Failed
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-4 mb-3 text-sm text-gray-400">
                        <span>{ing.total_docs} documents</span>
                        <span>·</span>
                        <span>{ing.entity_count} entities</span>
                        <span>·</span>
                        <span>
                          {new Date(ing.created_at).toLocaleDateString()}
                        </span>
                      </div>

                      {ing.message && (
                        <p className="text-sm text-gray-500 mb-3">{ing.message}</p>
                      )}

                      {ing.status === 'complete' && (
                        <div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => navigate('/dashboard')}
                              className="px-4 py-2 bg-gray-900 hover:bg-gray-800 border border-gray-800 rounded text-sm text-gray-300 hover:text-white transition-colors"
                            >
                              Ask Questions
                            </button>
                            <button
                              onClick={() => {
                                setDigestModal(ing.ingestion_id);
                                handleGenerateDigest(ing.ingestion_id, 7);
                              }}
                              className="px-4 py-2 bg-gray-900 hover:bg-gray-800 border border-gray-800 rounded text-sm text-gray-300 hover:text-white transition-colors"
                            >
                              Generate Digest
                            </button>
                            <button
                              onClick={() => handleDelete(ing.ingestion_id)}
                              className="px-4 py-2 bg-red-950/50 hover:bg-red-950 border border-red-900 rounded text-sm text-red-400 hover:text-red-300 transition-colors"
                            >
                              Delete
                            </button>
                          </div>

                          {/* Knowledge graph toggle */}
                          {ing.entity_count > 0 && (
                            <div className="mt-3">
                              <button
                                onClick={() =>
                                  setExpandedGraph(
                                    expandedGraph === ing.ingestion_id ? null : ing.ingestion_id
                                  )
                                }
                                className="text-xs text-blue-500 hover:text-blue-400 transition-colors"
                              >
                                {expandedGraph === ing.ingestion_id
                                  ? '▾ Hide knowledge graph'
                                  : '▸ Show knowledge graph'}
                              </button>

                              {expandedGraph === ing.ingestion_id && (
                                <div className="mt-2 h-64 rounded border border-gray-800 overflow-hidden">
                                  <MiniGraph ingestionId={ing.ingestion_id} />
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Digest Modal */}
      {digestModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-950 border border-gray-800 rounded-lg max-w-3xl w-full max-h-[80vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Digest</h2>
              <button
                onClick={() => {
                  setDigestModal(null);
                  setDigest(null);
                }}
                className="text-gray-500 hover:text-white"
              >
                ✕
              </button>
            </div>

            {digestLoading && (
              <div className="text-center py-8">
                <div className="inline-block w-8 h-8 border-2 border-gray-800 border-t-white rounded-full animate-spin mb-4"></div>
                <p className="text-gray-500">Generating digest...</p>
              </div>
            )}

            {digest && !digestLoading && (
              <div>
                <div className="mb-4 pb-4 border-b border-gray-800">
                  <h3 className="text-lg font-medium mb-1">{digest.source_name}</h3>
                  <p className="text-sm text-gray-500">{digest.period}</p>
                </div>

                <div className="space-y-4 mb-6">
                  {digest.sections.map((section, idx) => (
                    <div key={idx} className="bg-gray-900/50 rounded p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">{section.type}</h4>
                        <span className="text-sm text-gray-500">
                          {section.count} items
                        </span>
                      </div>
                      <p className="text-sm text-gray-400">{section.summary}</p>
                    </div>
                  ))}
                </div>

                {digest.stats && (
                  <div className="bg-gray-900/50 rounded p-4">
                    <h4 className="font-medium mb-2">Statistics</h4>
                    <div className="text-sm text-gray-400 space-y-1">
                      <p>Total documents: {digest.stats.total_docs}</p>
                      {digest.stats.date_range && (
                        <p>Date range: {digest.stats.date_range}</p>
                      )}
                      {digest.stats.top_authors && digest.stats.top_authors.length > 0 && (
                        <p>
                          Top contributors:{' '}
                          {digest.stats.top_authors
                            .slice(0, 3)
                            .map((a) => a.name)
                            .join(', ')}
                        </p>
                      )}
                    </div>
                  </div>
                )}

                <button
                  onClick={() => {
                    navigator.clipboard.writeText(
                      JSON.stringify(digest, null, 2)
                    );
                    alert('Digest copied to clipboard!');
                  }}
                  className="mt-4 w-full px-4 py-2 bg-gray-900 hover:bg-gray-800 border border-gray-800 rounded text-sm text-gray-300 hover:text-white transition-colors"
                >
                  Copy to Clipboard
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default IngestionPage;
