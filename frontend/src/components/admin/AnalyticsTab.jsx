import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function AnalyticsTab() {
  const [routerStats, setRouterStats] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [routerRes, analyticsRes] = await Promise.all([
        fetch('/api/admin/router-stats'),
        fetch('/api/admin/analytics')
      ]);

      setRouterStats(await routerRes.json());
      setAnalytics(await analyticsRes.json());
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
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

  const pipelineData = [
    { name: 'Normal RAG', value: routerStats?.normal_rag_count || 0, color: '#3b82f6' },
    { name: 'Agentic RAG', value: routerStats?.agentic_rag_count || 0, color: '#8b5cf6' }
  ];

  const dbUsageData = [
    { name: 'ChromaDB', value: analytics?.database_usage?.chromadb || 0 },
    { name: 'Neo4j', value: analytics?.database_usage?.neo4j || 0 },
    { name: 'Hybrid', value: analytics?.database_usage?.hybrid || 0 }
  ];

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Analytics</h1>
        <p className="text-gray-500">System performance and usage insights</p>
      </div>

      {/* Router Statistics */}
      <div className="mb-8">
        <h2 className="text-xs text-gray-500 uppercase tracking-wider mb-4">Pipeline Distribution</h2>
        <div className="grid grid-cols-2 gap-6">
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <h3 className="text-sm text-gray-400 mb-4">Query Routing</h3>
            {routerStats?.total_queries > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={pipelineData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {pipelineData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-600">
                No routing data yet
              </div>
            )}
          </div>

          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <h3 className="text-sm text-gray-400 mb-4">Statistics</h3>
            <div className="space-y-4">
              <div>
                <div className="text-gray-500 text-sm mb-1">Total Queries</div>
                <div className="text-3xl font-bold">{routerStats?.total_queries || 0}</div>
              </div>
              <div>
                <div className="text-gray-500 text-sm mb-1">Normal RAG</div>
                <div className="text-2xl font-bold text-blue-400">
                  {routerStats?.normal_rag_count || 0} ({routerStats?.normal_percentage?.toFixed(1) || 0}%)
                </div>
              </div>
              <div>
                <div className="text-gray-500 text-sm mb-1">Agentic RAG</div>
                <div className="text-2xl font-bold text-purple-400">
                  {routerStats?.agentic_rag_count || 0} ({routerStats?.agentic_percentage?.toFixed(1) || 0}%)
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Database Usage */}
      <div className="mb-8">
        <h2 className="text-xs text-gray-500 uppercase tracking-wider mb-4">Database Usage</h2>
        <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={dbUsageData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="name" stroke="#666" />
              <YAxis stroke="#666" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#111', border: '1px solid #333' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Query Volume */}
      {analytics?.query_volume?.length > 0 && (
        <div className="mb-8">
          <h2 className="text-xs text-gray-500 uppercase tracking-wider mb-4">Query Volume (Last 24h)</h2>
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={analytics.query_volume}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="time" stroke="#666" />
                <YAxis stroke="#666" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#111', border: '1px solid #333' }}
                  labelStyle={{ color: '#fff' }}
                />
                <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Recent Routing Decisions */}
      <div>
        <h2 className="text-xs text-gray-500 uppercase tracking-wider mb-4">Recent Routing Decisions</h2>
        <div className="space-y-2">
          {routerStats?.recent_decisions?.slice(0, 10).map((decision, idx) => (
            <div key={idx} className="bg-gray-950 border border-gray-800 rounded-lg p-4 flex items-start justify-between">
              <div className="flex-1">
                <div className="text-white mb-1">{decision.query}</div>
                <div className="text-sm text-gray-500">
                  {new Date(decision.timestamp).toLocaleString()}
                </div>
              </div>
              <span className={`px-3 py-1 rounded text-sm ${
                decision.pipeline === 'normal_rag'
                  ? 'bg-blue-900 text-blue-400'
                  : 'bg-purple-900 text-purple-400'
              }`}>
                {decision.pipeline}
              </span>
            </div>
          ))}

          {(!routerStats?.recent_decisions || routerStats.recent_decisions.length === 0) && (
            <div className="text-center py-8 text-gray-600">
              No routing decisions yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AnalyticsTab;
