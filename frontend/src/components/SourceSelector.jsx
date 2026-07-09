import { useState, useEffect } from 'react';

function SourceSelector({ onSourceChange, selectedSource }) {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      const response = await fetch('/api/ingest/list');
      if (response.ok) {
        const data = await response.json();
        // Only show completed ingestions
        const completedSources = data.ingestions.filter(
          (ing) => ing.status === 'complete'
        );
        setSources(completedSources);
      }
    } catch (error) {
      console.error('Failed to fetch sources:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const value = e.target.value;
    onSourceChange(value === 'all' ? null : value);
  };

  if (loading) {
    return (
      <div className="text-sm text-gray-500">Loading sources...</div>
    );
  }

  return (
    <div className="mb-4">
      <label className="block text-sm text-gray-500 mb-2 uppercase tracking-wider">
        Filter by Source
      </label>
      <select
        value={selectedSource || 'all'}
        onChange={handleChange}
        className="w-full px-4 py-2 bg-gray-950 border border-gray-800 rounded text-white focus:outline-none focus:border-gray-700"
      >
        <option value="all">All Sources</option>
        {sources.map((source) => (
          <option key={source.ingestion_id} value={source.ingestion_id}>
            {source.source_name} ({source.total_docs} docs)
          </option>
        ))}
      </select>
    </div>
  );
}

export default SourceSelector;
