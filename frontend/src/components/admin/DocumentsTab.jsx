import { useState, useEffect } from 'react';

function DocumentsTab() {
  const [content, setContent] = useState('');
  const [metadata, setMetadata] = useState('{"source": "admin", "type": "manual"}');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [chromaStats, setChromaStats] = useState(null);
  const [neo4jStats, setNeo4jStats] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const [chromaRes, neo4jRes] = await Promise.all([
        fetch('/api/admin/chromadb/stats'),
        fetch('/api/admin/neo4j/stats')
      ]);

      setChromaStats(await chromaRes.json());
      setNeo4jStats(await neo4jRes.json());
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleIngest = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      let metadataObj = {};
      try {
        metadataObj = JSON.parse(metadata);
      } catch {
        metadataObj = { source: 'admin' };
      }

      const response = await fetch('/api/admin/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content,
          metadata: metadataObj
        })
      });

      const data = await response.json();
      setResult(data);

      if (data.success) {
        setContent('');
        fetchStats(); // Refresh stats
      }
    } catch (error) {
      setResult({ success: false, message: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Document Management</h1>
        <p className="text-gray-500">Ingest documents and manage knowledge base</p>
      </div>

      {/* Current Stats */}
      <div className="mb-8">
        <h2 className="text-xs text-gray-500 uppercase tracking-wider mb-4">Current Data</h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <h3 className="text-sm text-gray-400 mb-4">ChromaDB</h3>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Total Documents:</span>
                <span className="text-white font-medium">{chromaStats?.total_documents || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Collections:</span>
                <span className="text-white font-medium">{chromaStats?.collections?.join(', ') || 'None'}</span>
              </div>
            </div>
          </div>

          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <h3 className="text-sm text-gray-400 mb-4">Neo4j Graph</h3>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Total Nodes:</span>
                <span className="text-white font-medium">{neo4jStats?.total_nodes || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Relationships:</span>
                <span className="text-white font-medium">{neo4jStats?.total_relationships || 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Ingestion Form */}
      <div>
        <h2 className="text-xs text-gray-500 uppercase tracking-wider mb-4">Ingest Document</h2>
        <form onSubmit={handleIngest} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Document Content</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter document content..."
              className="w-full px-4 py-3 bg-gray-950 border border-gray-800 rounded text-white placeholder-gray-700 focus:outline-none focus:border-gray-700 resize-none h-40"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Metadata (JSON)</label>
            <input
              type="text"
              value={metadata}
              onChange={(e) => setMetadata(e.target.value)}
              className="w-full px-4 py-3 bg-gray-950 border border-gray-800 rounded text-white placeholder-gray-700 focus:outline-none focus:border-gray-700"
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            disabled={loading || !content.trim()}
            className="px-6 py-2.5 bg-white text-black text-sm font-medium rounded hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-all uppercase tracking-wider"
          >
            {loading ? 'Ingesting...' : 'Ingest Document'}
          </button>
        </form>

        {/* Result */}
        {result && (
          <div className={`mt-4 p-4 rounded border ${
            result.success 
              ? 'bg-green-950/50 border-green-900 text-green-400'
              : 'bg-red-950/50 border-red-900 text-red-400'
          }`}>
            <div className="font-medium mb-1">{result.message}</div>
            {result.doc_id && (
              <div className="text-sm text-gray-500">Document ID: {result.doc_id}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default DocumentsTab;
