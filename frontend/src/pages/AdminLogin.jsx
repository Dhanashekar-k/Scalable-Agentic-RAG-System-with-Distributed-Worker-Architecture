import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function AdminLogin() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    
    // Simple password check (in production, use proper auth)
    if (password === 'admin123') {
      localStorage.setItem('adminAuth', 'true');
      navigate('/admin');
    } else {
      setError('Invalid password');
      setPassword('');
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-white mb-2">NIYANTA</h1>
          <p className="text-gray-500 text-sm uppercase tracking-wider">Admin Access</p>
        </div>

        <div className="bg-gray-950 border border-gray-800 rounded-lg p-8">
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm text-gray-400 mb-2 uppercase tracking-wider">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-black border border-gray-800 rounded text-white focus:outline-none focus:border-gray-700"
                placeholder="Enter admin password"
                autoFocus
              />
            </div>

            {error && (
              <div className="text-red-400 text-sm">{error}</div>
            )}

            <button
              type="submit"
              className="w-full px-6 py-3 bg-white text-black text-sm font-medium rounded hover:bg-gray-200 transition-all uppercase tracking-wider"
            >
              Access Dashboard
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-800">
            <button
              onClick={() => navigate('/')}
              className="text-sm text-gray-600 hover:text-gray-400 transition-colors"
            >
              ← Back to User Dashboard
            </button>
          </div>
        </div>

        <div className="mt-6 text-center text-xs text-gray-700">
          For demo: password is "admin123"
        </div>
      </div>
    </div>
  );
}

export default AdminLogin;
