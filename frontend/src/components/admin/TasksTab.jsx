import { useState, useEffect } from 'react';

function TasksTab() {
  const [tasks, setTasks] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTasks();
  }, [statusFilter]);

  const fetchTasks = async () => {
    try {
      const url = statusFilter 
        ? `/api/admin/tasks?status=${statusFilter}`
        : '/api/admin/tasks';
      
      const response = await fetch(url);
      const data = await response.json();
      setTasks(data.tasks || []);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async (taskId) => {
    try {
      const response = await fetch(`/api/admin/tasks/${taskId}/retry`, {
        method: 'POST'
      });
      const result = await response.json();
      alert(result.message);
      fetchTasks();
    } catch (error) {
      alert('Failed to retry task: ' + error.message);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-400';
      case 'failed': return 'text-red-400';
      case 'processing': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Async Tasks</h1>
        <p className="text-gray-500">Monitor and manage background tasks</p>
      </div>

      {/* Filter */}
      <div className="mb-6 flex gap-2">
        <button
          onClick={() => setStatusFilter('')}
          className={`px-4 py-2 text-sm rounded ${
            statusFilter === '' ? 'bg-white text-black' : 'bg-gray-900 text-gray-400'
          }`}
        >
          All
        </button>
        <button
          onClick={() => setStatusFilter('completed')}
          className={`px-4 py-2 text-sm rounded ${
            statusFilter === 'completed' ? 'bg-white text-black' : 'bg-gray-900 text-gray-400'
          }`}
        >
          Completed
        </button>
        <button
          onClick={() => setStatusFilter('failed')}
          className={`px-4 py-2 text-sm rounded ${
            statusFilter === 'failed' ? 'bg-white text-black' : 'bg-gray-900 text-gray-400'
          }`}
        >
          Failed
        </button>
        <button
          onClick={() => setStatusFilter('processing')}
          className={`px-4 py-2 text-sm rounded ${
            statusFilter === 'processing' ? 'bg-white text-black' : 'bg-gray-900 text-gray-400'
          }`}
        >
          Processing
        </button>
      </div>

      {/* Tasks List */}
      <div className="space-y-3">
        {tasks.map((task) => (
          <div key={task.task_id} className="bg-gray-950 border border-gray-800 rounded-lg p-4">
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <div className="text-white mb-1">{task.query}</div>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span className={getStatusColor(task.status)}>{task.status}</span>
                  {task.pipeline && <span>• {task.pipeline}</span>}
                  <span>• {new Date(task.created_at).toLocaleString()}</span>
                </div>
              </div>
              {task.status === 'failed' && (
                <button
                  onClick={() => handleRetry(task.task_id)}
                  className="px-4 py-1.5 bg-white text-black text-sm rounded hover:bg-gray-200"
                >
                  Retry
                </button>
              )}
            </div>
            {task.error && (
              <div className="mt-2 text-sm text-red-400 bg-red-950/30 rounded p-2">
                Error: {task.error}
              </div>
            )}
          </div>
        ))}

        {tasks.length === 0 && !loading && (
          <div className="text-center py-12 text-gray-600">
            No tasks found
          </div>
        )}
      </div>
    </div>
  );
}

export default TasksTab;
