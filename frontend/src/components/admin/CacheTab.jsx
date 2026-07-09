import { useState, useEffect } from 'react';

function CacheTab() {
  const [stats, setStats] = useState(null);
  const [cacheKeys, setCacheKeys] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, keysRes] = await Promise.all([
        fetch('/api/cache/stats'),
        fetch('/api/cache/keys?limit=20')
      ]);

      setStats(await statsRes.json());
      setCacheKeys(await keysRes.json());
    } catch (error) {
      console.error('Failed to fetch cache data:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim() || searchQuery.length < 2) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/cache/search?q=${encodeURIComponent(searchQuery)}`);
      const data = await response.json();
      setSearchResults(data);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClearAll = async () => {
    if (!confirm('Are you sure you want to clear all cache? This cannot be undone.')) return;

    try {
      const response = await fetch('/api/cache/clear', { method: 'POST' });
      const result = await response.json();
      alert(result.message);
      fetchData();
      setSearchResults(null);
    } catch (error) {
      alert('Failed to clear cache: ' + error.message);
    }
  };

  const handleDeleteQuery = async (query) => {
    try {
      const response = await fetch(`/api/cache/query?query=${encodeURIComponent(query)}`, {
        method: 'DELETE'
      });
      const result = await response.json();
      
      if (result.success) {
        fetchData();
        if (searchResults) {
          setSearchResults({
            ...searchResults,
            items: searchResults.items.filter(item => item.query !== query)
          });
        }
      }
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Cache Management</h1>
        <p className="text-gray-500">Monitor and manage semantic cache</p>
      </div>

      {/* Cache Stats */}
      <div className="mb-8">
        <h2 className="text-xs text-gray-500 uppercase tracking-wider mb-4">Cache Statistics</h2>
        <div className="grid grid-cols-5 gap-4">
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400 mb-1">Total Queries</div>
            <div className="text-2xl font-bold">{stats?.total_queries || 0}</div>
          </div>
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400 mb-1">Cache Hits</div>
            <div className="text-2xl font-bold text-green-400">{stats?.cache_hits || 0}</div>
          </div>
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400 mb-1">Cache Misses</div>
            <div className="text-2xl font-bold text-red-400">{stats?.cache_misses || 0}</div>
          </div>
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400 mb-1">Hit Rate</div>
            <div className="text-2xl font-bold">{(stats?.hit_rate * 100 || 0).toFixed(1)}%</div>
          </div>
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400 mb-1">Avg Similarity</div>
            <div className="text-2xl font-bold">{(stats?.avg_similarity * 100 || 0).toFixed(1)}%</div>
          </div>
        </div>
      </div>

      {/* Search & Actions */}
      <div className="mb-8 flex gap-4">
        <div className="flex-1 flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search cached queries..."
            className="flex-1 px-4 py-2 bg-gray-950 border border-gray-800 rounded text-white placeholder-gray-700 focus:outline-none focus:border-gray-700"
          />
          <button
            onClick={handleSearch}
            disabled={loading || searchQuery.length < 2}
            className="px-6 py-2 bg-white text-black text-sm font-medium rounded hover:bg-gray-200 disabled:opacity-30 uppercase tracking-wider"
          >
            Search
          </button>
        </div>
        <button
          onClick={handleClearAll}
          className="px-6 py-2 bg-red-900 text-white text-sm font-medium rounded hover:bg-red-800 uppercase tracking-wider"
        >
          Clear All Cache
        </button>
      </div>

      {/* Search Results / Cache Keys */}
      <div>
        <h2 className="text-xs text-gray-500 uppercase tracking-wider mb-4">
          {searchResults ? `Search Results (${searchResults.total})` : `Recent Cache Keys (${cacheKeys.total || 0})`}
        </h2>
        <div className="space-y-2">
          {(searchResults?.items || cacheKeys?.items || []).map((item, idx) => (
            <div key={idx} className="bg-gray-950 border border-gray-800 rounded-lg p-4 flex justify-between items-start">
              <div className="flex-1">
                <div className="text-white mb-1">{item.query}</div>
                <div className="text-sm text-gray-500 line-clamp-1">{item.answer_preview}</div>
                {item.confidence && (
                  <div className="text-xs text-gray-600 mt-1">
                    Confidence: {(item.confidence * 100).toFixed(1)}%
                  </div>
                )}
              </div>
              <button
                onClick={() => handleDeleteQuery(item.query)}
                className="ml-4 text-red-500 hover:text-red-400 text-sm"
              >
                Delete
              </button>
            </div>
          ))}

          {(searchResults?.items || cacheKeys?.items || []).length === 0 && (
            <div className="text-center py-8 text-gray-600">
              {searchResults ? 'No results found' : 'No cached queries'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CacheTab;
