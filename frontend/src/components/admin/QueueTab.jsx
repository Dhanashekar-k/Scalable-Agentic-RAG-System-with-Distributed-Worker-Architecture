import { useState, useEffect } from 'react';

function QueueTab() {
  const [queueStatus, setQueueStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchQueue = async () => {
    try {
      const response = await fetch('/api/admin/rabbitmq/status');
      const data = await response.json();
      setQueueStatus(data);
    } catch (error) {
      console.error('Failed to fetch queue status:', error);
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
        <h1 className="text-3xl font-bold mb-2">RabbitMQ Queue</h1>
        <p className="text-gray-500">Monitor message queue status</p>
      </div>

      <div className="mb-8">
        <h2 className="text-xs text-gray-500 uppercase tracking-wider mb-4">Queue Status</h2>
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <div className="text-sm text-gray-400 mb-1">Queue Name</div>
            <div className="text-xl font-bold">{queueStatus?.queue_name || 'N/A'}</div>
          </div>
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <div className="text-sm text-gray-400 mb-1">Messages Ready</div>
            <div className="text-3xl font-bold">{queueStatus?.messages_ready || 0}</div>
          </div>
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <div className="text-sm text-gray-400 mb-1">Consumers</div>
            <div className="text-3xl font-bold">{queueStatus?.consumers || 0}</div>
          </div>
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <div className="text-sm text-gray-400 mb-1">Total Messages</div>
            <div className="text-3xl font-bold">{queueStatus?.total_messages || 0}</div>
          </div>
        </div>
      </div>

      <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
        <h3 className="text-sm text-gray-400 mb-4">Queue Information</h3>
        <div className="space-y-3 text-sm">
          <div className="flex items-start gap-3">
            <span className="text-gray-600">→</span>
            <div>
              <div className="text-gray-400 mb-1">Status</div>
              <div className="text-white">
                {queueStatus?.consumers > 0 ? 'Active - Workers consuming' : 'Idle - No workers'}
              </div>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <span className="text-gray-600">→</span>
            <div>
              <div className="text-gray-400 mb-1">Processing</div>
              <div className="text-white">
                {queueStatus?.messages_ready > 0 
                  ? `${queueStatus.messages_ready} messages pending`
                  : 'All messages processed'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default QueueTab;
