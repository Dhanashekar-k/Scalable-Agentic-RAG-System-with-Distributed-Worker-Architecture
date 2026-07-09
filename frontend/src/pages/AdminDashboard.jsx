import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import OverviewTab from '../components/admin/OverviewTab';
import DocumentsTab from '../components/admin/DocumentsTab';
import CacheTab from '../components/admin/CacheTab';
import QueueTab from '../components/admin/QueueTab';
import AnalyticsTab from '../components/admin/AnalyticsTab';
import TasksTab from '../components/admin/TasksTab';
import KnowledgeGraphTab from '../components/admin/KnowledgeGraphTab';

function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const navigate = useNavigate();

  useEffect(() => {
    // Check auth
    const isAuth = localStorage.getItem('adminAuth');
    if (!isAuth) {
      navigate('/admin/login');
    }
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('adminAuth');
    navigate('/admin/login');
  };

  const tabs = [
    { id: 'overview', name: 'Overview' },
    { id: 'documents', name: 'Documents' },
    { id: 'cache', name: 'Cache' },
    { id: 'queue', name: 'Queue' },
    { id: 'tasks', name: 'Tasks' },
    { id: 'analytics', name: 'Analytics' },
    { id: 'graph', name: '🕸 Knowledge Graph' },
  ];

  const renderTab = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab onViewGraph={() => setActiveTab('graph')} />;
      case 'documents':
        return <DocumentsTab />;
      case 'cache':
        return <CacheTab />;
      case 'queue':
        return <QueueTab />;
      case 'tasks':
        return <TasksTab />;
      case 'analytics':
        return <AnalyticsTab />;
      case 'graph':
        return <KnowledgeGraphTab />;
      default:
        return <OverviewTab onViewGraph={() => setActiveTab('graph')} />;
    }
  };

  return (
    <div className="flex h-screen bg-black text-white">
      {/* Sidebar */}
      <aside className="w-64 border-r border-gray-800 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-800">
          <h1 className="text-xl font-bold mb-1">NIYANTA</h1>
          <p className="text-xs text-gray-500 uppercase tracking-wider">Admin Console</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <div className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full text-left px-3 py-2.5 rounded text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'bg-gray-900 text-white'
                    : 'text-gray-400 hover:text-gray-300 hover:bg-gray-900/50'
                }`}
              >
                {tab.name}
              </button>
            ))}
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-800 space-y-2">
          <a
            href="http://localhost:3000"
            target="_blank"
            rel="noopener noreferrer"
            className="block w-full text-left px-3 py-2 text-sm text-gray-600 hover:text-blue-400 transition-colors"
          >
            📊 View Metrics
          </a>
          <button
            onClick={() => navigate('/')}
            className="w-full text-left px-3 py-2 text-sm text-gray-600 hover:text-gray-400 transition-colors"
          >
            ← User Dashboard
          </button>
          <button
            onClick={handleLogout}
            className="w-full text-left px-3 py-2 text-sm text-gray-600 hover:text-red-400 transition-colors"
          >
            ⏏ Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        {renderTab()}
      </main>
    </div>
  );
}

export default AdminDashboard;
