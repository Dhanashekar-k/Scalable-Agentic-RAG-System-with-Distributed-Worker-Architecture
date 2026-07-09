import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAuth } from '../context/AuthContext';
import SourceSelector from '../components/SourceSelector';
import '../App.css';

function UserDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [selectedHistory, setSelectedHistory] = useState(null);
  const [sourceFilter, setSourceFilter] = useState(null);

  // Load history from localStorage per user
  useEffect(() => {
    if (user) {
      const userHistoryKey = `niyanta_history_${user.id}`;
      const savedHistory = localStorage.getItem(userHistoryKey);
      if (savedHistory) {
        try {
          setHistory(JSON.parse(savedHistory));
        } catch (e) {
          localStorage.removeItem(userHistoryKey);
        }
      }
    }
  }, [user]);

  // Save history to localStorage whenever it changes
  useEffect(() => {
    if (user && history.length > 0) {
      const userHistoryKey = `niyanta_history_${user.id}`;
      localStorage.setItem(userHistoryKey, JSON.stringify(history));
    }
  }, [history, user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': user?.id || 'anonymous',
          'X-Session-Token': user?.sessionToken || '',
        },
        body: JSON.stringify({
          query: query,
          use_cache: true,
          force_agentic: false,
          user_id: user?.id,
          username: user?.username,
          source_filter: sourceFilter,
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      setResponse(data);
      setSelectedHistory(null);
      
      const newHistoryItem = { 
        id: Date.now(),
        query, 
        response: data, 
        timestamp: new Date() 
      };
      setHistory([newHistoryItem, ...history.slice(0, 19)]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const selectHistoryItem = (item) => {
    setSelectedHistory(item);
    setQuery(item.query);
    setResponse(item.response);
  };

  const clearHistory = () => {
    setHistory([]);
    setSelectedHistory(null);
  };

  const displayResponse = selectedHistory?.response || response;

  return (
    <div className="flex h-screen bg-black text-white">
      {/* Left Sidebar */}
      <aside className="w-80 border-r border-gray-800 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-center gap-3 mb-1">
            <div className="text-2xl font-bold">NIYANTA</div>
          </div>
          <div className="text-xs text-gray-500 uppercase tracking-wider">Query Dashboard</div>
        </div>

        {/* User Info */}
        <div className="px-6 py-4 border-b border-gray-800 bg-gray-900/30">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Current User</div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-white">{user?.username || 'Guest'}</div>
              <div className="text-xs text-gray-600 font-mono">{user?.id?.slice(0, 12)}...</div>
            </div>
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          </div>
        </div>

        {/* History List */}
        <div className="flex-1 overflow-y-auto">
          {history.length > 0 ? (
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs text-gray-500 uppercase tracking-wider">Recent Queries</h3>
                <button 
                  onClick={clearHistory}
                  className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
                >
                  Clear
                </button>
              </div>
              <div className="space-y-1">
                {history.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => selectHistoryItem(item)}
                    className={`w-full text-left px-3 py-2.5 rounded text-sm transition-colors ${
                      selectedHistory?.id === item.id
                        ? 'bg-gray-900 text-white'
                        : 'text-gray-400 hover:text-gray-300 hover:bg-gray-900/50'
                    }`}
                  >
                    <div className="line-clamp-2 leading-relaxed">{item.query}</div>
                    <div className="text-xs text-gray-600 mt-1">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-6 text-center">
              <div className="text-gray-600 text-sm">No queries yet</div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-800 space-y-3">
          <button
            onClick={() => navigate('/ingest')}
            className="w-full py-2 px-3 bg-gray-900 hover:bg-gray-800 border border-gray-800 rounded text-sm text-gray-400 hover:text-white transition-colors"
          >
            📥 Manage Sources
          </button>
          <button
            onClick={() => {
              logout();
              navigate('/');
            }}
            className="w-full py-2 px-3 bg-gray-900 hover:bg-gray-800 border border-gray-800 rounded text-sm text-gray-400 hover:text-white transition-colors"
          >
            Logout
          </button>
          <div className="text-xs text-gray-600 leading-relaxed">
            Powered by Agentic RAG
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="px-8 py-6 border-b border-gray-800">
          <h1 className="text-3xl font-bold mb-2"> Agentic RAG System</h1>
          <p className="text-gray-500">
            Ask questions and get AI-powered answers
          </p>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-8">
          {/* Query Form */}
          <div className="max-w-4xl">
            <form onSubmit={handleSubmit} className="mb-8">
              <SourceSelector
                onSourceChange={setSourceFilter}
                selectedSource={sourceFilter}
              />
              <div className="mb-4">
                <label className="block text-sm text-gray-500 mb-3 uppercase tracking-wider">
                  Your Query
                </label>
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="What is a mutual fund?"
                  className="w-full px-4 py-3 bg-gray-950 border border-gray-800 rounded text-white placeholder-gray-700 focus:outline-none focus:border-gray-700 resize-none h-24"
                  disabled={loading}
                />
              </div>
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="px-6 py-2.5 bg-white text-black text-sm font-medium rounded hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-all uppercase tracking-wider"
              >
                {loading ? 'Processing...' : 'Submit Query'}
              </button>
            </form>

            {/* Error */}
            {error && (
              <div className="mb-8 p-4 bg-red-950/50 border border-red-900 rounded text-red-400">
                Error: {error}
              </div>
            )}

            {/* Response */}
            {displayResponse && (
              <div className="space-y-6">
                {/* Main Answer */}
                <div>
                  <h2 className="text-xs text-gray-500 uppercase tracking-wider mb-4">Response</h2>
                  <div className="bg-gray-950 border border-gray-800 rounded p-6 prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {displayResponse.answer}
                    </ReactMarkdown>
                  </div>
                </div>

                {/* Metadata Grid */}
                <div>
                  <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-4">Key Highlights</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-start gap-3">
                      <div className="text-gray-600">→</div>
                      <div>
                        <div className="text-sm text-gray-400 mb-1">Pipeline Mode</div>
                        <div className="text-white font-medium">{displayResponse.pipeline}</div>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="text-gray-600">→</div>
                      <div>
                        <div className="text-sm text-gray-400 mb-1">Cache Status</div>
                        <div className="text-white font-medium">
                          {displayResponse.cache_hit ? 'Cached' : 'Fresh Query'}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="text-gray-600">→</div>
                      <div>
                        <div className="text-sm text-gray-400 mb-1">Confidence Score</div>
                        <div className="text-white font-medium">
                          {(displayResponse.confidence * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="text-gray-600">→</div>
                      <div>
                        <div className="text-sm text-gray-400 mb-1">Processing Time</div>
                        <div className="text-white font-medium">
                          {displayResponse.processing_time_ms?.toFixed(0) || 0}ms
                        </div>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="text-gray-600">→</div>
                      <div>
                        <div className="text-sm text-gray-400 mb-1">Source Documents</div>
                        <div className="text-white font-medium">
                          {displayResponse.sources?.length || 0} documents
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Technologies/Sources */}
                {displayResponse.sources && displayResponse.sources.length > 0 && (
                  <div>
                    <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-4">Sources</h3>
                    <div className="space-y-3">
                      {displayResponse.sources.slice(0, 5).map((source, idx) => (
                        <div key={idx} className="bg-gray-950 border border-gray-800 rounded p-4">
                          {source.source_url && source.source_id && (
                            <div className="mb-2">
                              <a
                                href={source.source_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-blue-400 hover:text-blue-300 font-medium"
                              >
                                {source.source_id}
                              </a>
                            </div>
                          )}
                          <p className="text-sm text-gray-400 mb-2 line-clamp-2">
                            {source.content}
                          </p>
                          {source.metadata && (
                            <div className="flex flex-wrap gap-2">
                              {source.metadata.source && (
                                <span className="px-2.5 py-1 bg-gray-900 text-gray-500 text-xs rounded border border-gray-800">
                                  {source.metadata.source}
                                </span>
                              )}
                              {source.metadata.type && (
                                <span className="px-2.5 py-1 bg-gray-900 text-gray-500 text-xs rounded border border-gray-800">
                                  {source.metadata.type}
                                </span>
                              )}
                              {source.source_type && (
                                <span className="px-2.5 py-1 bg-gray-900 text-gray-500 text-xs rounded border border-gray-800">
                                  {source.source_type}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Empty State */}
            {!displayResponse && !loading && (
              <div className="text-center py-16 text-gray-600">
                <p className="text-lg">Enter a query to get started</p>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="text-center py-16">
                <div className="inline-block w-8 h-8 border-2 border-gray-800 border-t-white rounded-full animate-spin mb-4"></div>
                <p className="text-gray-500">Analyzing your query...</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default UserDashboard;
