import { useState, useEffect } from 'react';

export function SplashLoader({ onComplete }) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          // Give 500ms extra for full animation
          setTimeout(onComplete, 500);
          return 100;
        }
        return prev + Math.random() * 30;
      });
    }, 200);

    return () => clearInterval(interval);
  }, [onComplete]);

  return (
    <div className="fixed inset-0 bg-black flex items-center justify-center z-50">
      {/* Animated background gradient */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-cyan-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-teal-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
      </div>

      {/* Loader Content */}
      <div className="relative z-10 text-center space-y-8">
        {/* Logo */}
        <div className="space-y-4">
          <h1 className="text-6xl font-bold tracking-widest">
            <span className="bg-gradient-to-r from-cyan-400 via-teal-500 to-cyan-500 bg-clip-text text-transparent animate-pulse">
              NIYANTA
            </span>
          </h1>
          <div className="text-gray-500 text-sm tracking-widest uppercase">
            Intelligent RAG System
          </div>
        </div>

        {/* Loading Animation */}
        <div className="flex justify-center">
          <div className="relative w-16 h-16">
            {/* Outer rotating ring */}
            <div
              className="absolute inset-0 rounded-full border-2 border-transparent border-t-cyan-500 border-r-teal-500"
              style={{
                animation: 'spin 2s linear infinite',
              }}
            ></div>
            {/* Middle rotating ring */}
            <div
              className="absolute inset-2 rounded-full border-2 border-transparent border-l-cyan-500 border-b-teal-500"
              style={{
                animation: 'spin 3s linear infinite reverse',
              }}
            ></div>
            {/* Inner pulsing dot */}
            <div className="absolute inset-4 rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 animate-pulse"></div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-64 space-y-2">
          <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 via-teal-500 to-cyan-500 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(progress, 100)}%` }}
            ></div>
          </div>
          <div className="text-gray-600 text-xs font-mono">
            {Math.min(Math.floor(progress), 100)}%
          </div>
        </div>

        {/* Status Text */}
        <div className="text-gray-500 text-sm space-y-1">
          <p>Initializing system...</p>
          <p className="text-xs text-gray-600">Please wait while we prepare your experience</p>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
