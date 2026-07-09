import { useState, useEffect } from 'react';

function OverviewTab({ onViewGraph }) {
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, healthRes] = await Promise.all([
        fetch('/api/admin/stats'),
        fetch('/api/admin/health-detailed')
      ]);

      const statsData = await statsRes.json();
      const healthData = await healthRes.json();

      setStats(statsData);
      setHealth(healthData);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">System Overview</h1>
        <p className="text-gray-500">Real-time system status and metrics</p>
      </div>

      {/* System Health */}
      <div className="mb-8">
        <h2 className="text-xs text-gray-500 uppercase tracking-wider mb-4">Service Health</h2>
        <div className="grid grid-cols-4 gap-4">
          {health?.services.map((service) => (
            <div
              key={service.name}
              className="bg-gray-950 border border-gray-800 rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">{service.name}</span>
                <span className={`w-2 h-2 rounded-full ${service.healthy ? 'bg-green-500' : 'bg-red-500'}`}></span>
              </div>
              <div className={`text-lg font-medium ${service.healthy ? 'text-green-400' : 'text-red-400'}`}>
                {service.status}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="mb-8">
        <h2 className="text-xs text-gray-500 uppercase tracking-wider mb-4">Key Metrics</h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <div className="text-sm text-gray-400 mb-1">Total Queries</div>
            <div className="text-3xl font-bold">{stats?.total_queries || 0}</div>
          </div>
          
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <div className="text-sm text-gray-400 mb-1">Cache Hit Rate</div>
            <div className="text-3xl font-bold">{(stats?.cache_hit_rate * 100 || 0).toFixed(1)}%</div>
          </div>
          
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <div className="text-sm text-gray-400 mb-1">Avg Response Time</div>
            <div className="text-3xl font-bold">{stats?.avg_response_time_ms?.toFixed(0) || 0}ms</div>
          </div>
          
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <div className="text-sm text-gray-400 mb-1">Active Tasks</div>
            <div className="text-3xl font-bold">{stats?.active_tasks || 0}</div>
          </div>
          
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <div className="text-sm text-gray-400 mb-1">ChromaDB Documents</div>
            <div className="text-3xl font-bold">{stats?.chromadb_docs || 0}</div>
          </div>
          
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <div className="text-sm text-gray-400 mb-1">Knowledge Graph</div>
            <div className="text-3xl font-bold">{stats?.neo4j_nodes || 0}</div>
            <div className="text-xs text-gray-600 mt-1">
              {stats?.neo4j_nodes || 0} nodes · {stats?.neo4j_relationships || 0} relationships
            </div>
            {onViewGraph && (
              <button
                onClick={onViewGraph}
                className="mt-2 text-xs text-blue-500 hover:text-blue-400 transition-colors"
              >
                View Graph →
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Database Stats */}
      <div>
        <h2 className="text-xs text-gray-500 uppercase tracking-wider mb-4">Database Information</h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <h3 className="text-sm text-gray-400 mb-3">ChromaDB</h3>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Total Documents:</span>
                <span className="text-white font-medium">{stats?.chromadb_docs || 0}</span>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <h3 className="text-sm text-gray-400 mb-3">Neo4j</h3>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Nodes:</span>
                <span className="text-white font-medium">{stats?.neo4j_nodes || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Relationships:</span>
                <span className="text-white font-medium">{stats?.neo4j_relationships || 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default OverviewTab;
