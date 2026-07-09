import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useEffect, useState } from 'react';
import { SplashLoader } from '../components/SplashLoader';
import { ArchitectureDiagram } from '../components/ArchitectureDiagram';

function LandingPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [showLoader, setShowLoader] = useState(true);
  const [showDocs, setShowDocs] = useState(false);

  // Redirect to dashboard if already logged in
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  if (showLoader) {
    return <SplashLoader onComplete={() => setShowLoader(false)} />;
  }

  return (
    <div className="min-h-screen bg-black text-white overflow-hidden">
      {/* Navigation */}
      <nav className="border-b border-gray-900 backdrop-blur-md fixed w-full z-50 bg-black/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="text-2xl font-bold tracking-widest">
            <span className="bg-gradient-to-r from-cyan-400 via-teal-500 to-cyan-500 bg-clip-text text-transparent hover:from-cyan-300 hover:to-cyan-300 transition-all duration-300">
              NIYANTA
            </span>
          </div>
          <div className="flex items-center gap-4">
            <button className="px-5 py-2 text-sm text-gray-400 hover:text-white transition-colors duration-300">
              Features
            </button>
            <button
              onClick={() => navigate('/login')}
              className="px-6 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 transition-all duration-300 font-medium text-sm shadow-lg hover:shadow-cyan-500/20"
            >
              Sign In
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center pt-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-cyan-600 rounded-full mix-blend-multiply filter blur-3xl opacity-15 animate-blob"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-teal-600 rounded-full mix-blend-multiply filter blur-3xl opacity-15 animate-blob animation-delay-2000"></div>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 w-80 h-80 bg-cyan-500 rounded-full mix-blend-multiply filter blur-3xl opacity-15 animate-blob animation-delay-4000"></div>
        </div>

        {/* Grid Background */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute inset-0" style={{
            backgroundImage: 'linear-gradient(90deg, #fff 1px, transparent 1px), linear-gradient(#fff 1px, transparent 1px)',
            backgroundSize: '50px 50px',
          }}></div>
        </div>

        {/* Content */}
        <div className="relative max-w-7xl mx-auto w-full">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            {/* Left Content */}
            <div className="space-y-8 animate-fadeInLeft">
              <div className="space-y-4">
                <div className="inline-block">
                  <div className="px-4 py-2 rounded-full border border-cyan-500/30 bg-cyan-500/5 backdrop-blur">
                    <span className="text-sm font-mono text-cyan-400">intelligent.retrieval.system</span>
                  </div>
                </div>
                <h1 className="text-6xl sm:text-7xl lg:text-8xl font-bold leading-tight">
                  <span className="block text-white">Advanced</span>
                  <span className="block">
                    <span className="bg-gradient-to-r from-cyan-400 via-teal-500 to-cyan-500 bg-clip-text text-transparent">
                      RAG Engine
                    </span>
                  </span>
                  <span className="block text-white">for Precision</span>
                </h1>
                <p className="text-lg text-gray-400 max-w-lg leading-relaxed pt-4">
                  Intelligent query routing with multi-step reasoning capabilities. Experience advanced retrieval-augmented generation with distributed worker architecture.
                </p>
              </div>

              {/* Feature List */}
              <div className="grid grid-cols-2 gap-4 max-w-md">
                {[
                  { label: 'Query Routing', desc: 'Intelligent complexity detection' },
                  { label: 'Multi-Step', desc: 'Advanced reasoning pipeline' },
                  { label: 'Distributed', desc: 'Scalable worker execution' },
                  { label: 'Caching', desc: 'Optimized performance layer' },
                ].map((item, i) => (
                  <div
                    key={i}
                    className="group px-4 py-3 rounded-lg border border-gray-800 hover:border-cyan-500/50 bg-gray-900/40 backdrop-blur hover:bg-gray-900/60 transition-all duration-300 cursor-pointer"
                  >
                    <div className="text-xs font-mono text-cyan-400 group-hover:text-cyan-300 transition-colors">
                      {item.label}
                    </div>
                    <div className="text-xs text-gray-500 mt-1 group-hover:text-gray-400 transition-colors">
                      {item.desc}
                    </div>
                  </div>
                ))}
              </div>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 pt-4">
                <button
                  onClick={() => navigate('/login')}
                  className="px-8 py-3 rounded-lg bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 transition-all duration-300 font-medium text-white shadow-lg hover:shadow-cyan-500/30 transform hover:scale-105 active:scale-95"
                >
                  Get Started
                </button>
                <button onClick={() => setShowDocs(true)} className="px-8 py-3 rounded-lg border border-gray-700 hover:border-cyan-500 text-gray-300 hover:text-white transition-all duration-300 font-medium backdrop-blur hover:bg-gray-900/50">
                  Documentation
                </button>
              </div>
            </div>

            {/* Right Side - Architecture Diagram */}
            <div className="animate-fadeInRight">
              <ArchitectureDiagram />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative py-24 px-4 sm:px-6 lg:px-8 border-t border-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20 space-y-4">
            <div className="inline-block">
              <div className="px-4 py-2 rounded-full border border-cyan-500/30 bg-cyan-500/5 backdrop-blur">
                <span className="text-sm font-mono text-cyan-400">dual-pipeline-system</span>
              </div>
            </div>
            <h2 className="text-5xl sm:text-6xl font-bold">
              Intelligent Query Processing
            </h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              Two optimized pathways for different query complexities. Choose the best execution strategy automatically.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Normal RAG Card */}
            <div className="group relative bg-gradient-to-br from-gray-900 to-gray-950 border border-gray-800 rounded-xl p-8 hover:border-cyan-500/50 transition-all duration-300 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-teal-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              <div className="relative z-10 space-y-6">
                <div className="space-y-2">
                  <div className="inline-block px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30">
                    <span className="text-xs font-mono text-cyan-400">FAST-PATH</span>
                  </div>
                  <h3 className="text-2xl font-bold">Standard RAG</h3>
                </div>
                
                <p className="text-gray-400 leading-relaxed">
                  Optimized for straightforward queries requiring direct answers and minimal reasoning steps.
                </p>
                
                <ul className="space-y-3 text-gray-400 text-sm">
                  <li className="flex items-start gap-3">
                    <span className="text-cyan-400 font-mono mt-0.5">→</span>
                    <span>Vector similarity search with ChromaDB</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-cyan-400 font-mono mt-0.5">→</span>
                    <span>Direct LLM answer generation</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-cyan-400 font-mono mt-0.5">→</span>
                    <span>Latency: ~1 second</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-cyan-400 font-mono mt-0.5">→</span>
                    <span>Ideal for factual retrieval</span>
                  </li>
                </ul>

                <div className="pt-4 border-t border-gray-800">
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Throughput</span>
                    <span className="text-cyan-400 font-mono">High</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Agentic RAG Card */}
            <div className="group relative bg-gradient-to-br from-gray-900 to-gray-950 border border-gray-800 rounded-xl p-8 hover:border-teal-500/50 transition-all duration-300 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-teal-500/10 to-cyan-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              <div className="relative z-10 space-y-6">
                <div className="space-y-2">
                  <div className="inline-block px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30">
                    <span className="text-xs font-mono text-teal-400">REASONING-PATH</span>
                  </div>
                  <h3 className="text-2xl font-bold">Agentic RAG</h3>
                </div>
                
                <p className="text-gray-400 leading-relaxed">
                  Advanced multi-step reasoning pipeline for complex queries requiring deep analysis and relationships.
                </p>
                
                <ul className="space-y-3 text-gray-400 text-sm">
                  <li className="flex items-start gap-3">
                    <span className="text-teal-400 font-mono mt-0.5">→</span>
                    <span>LangGraph state machine planning</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-teal-400 font-mono mt-0.5">→</span>
                    <span>Hybrid vector and graph retrieval</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-teal-400 font-mono mt-0.5">→</span>
                    <span>Latency: ~4-5 seconds</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-teal-400 font-mono mt-0.5">→</span>
                    <span>Best for complex analysis</span>
                  </li>
                </ul>

                <div className="pt-4 border-t border-gray-800">
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Reasoning Depth</span>
                    <span className="text-teal-400 font-mono">Advanced</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <div className="relative bg-gradient-to-r from-cyan-600/20 to-teal-600/20 border border-cyan-500/30 rounded-2xl p-12 backdrop-blur overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-teal-500/5"></div>
            
            <div className="relative z-10 text-center space-y-6">
              <h2 className="text-4xl font-bold">
                Ready to Experience Advanced RAG?
              </h2>
              <p className="text-gray-400 text-lg max-w-xl mx-auto">
                Deploy intelligent retrieval-augmented generation with distributed processing and advanced reasoning capabilities.
              </p>
              <button
                onClick={() => navigate('/login')}
                className="px-8 py-4 rounded-lg bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 transition-all duration-300 font-medium text-white shadow-lg hover:shadow-cyan-500/40 transform hover:scale-105 active:scale-95"
              >
                Start Building Today
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative border-t border-gray-900 py-12 px-4 sm:px-6 lg:px-8 backdrop-blur">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-3 gap-12 mb-8">
            {/* Brand */}
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-white">
                <span className="bg-gradient-to-r from-cyan-400 via-teal-500 to-cyan-500 bg-clip-text text-transparent">
                  NIYANTA
                </span>
              </h3>
              <p className="text-sm text-gray-500">
                Advanced retrieval-augmented generation system with intelligent routing and distributed execution.
              </p>
            </div>

            {/* Resources */}
            <div className="space-y-4">
              <h4 className="text-sm font-mono text-gray-400 uppercase tracking-wider">Resources</h4>
              <ul className="space-y-2 text-sm text-gray-500">
                <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
                <li><a href="#" className="hover:text-white transition-colors">API Reference</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Getting Started</a></li>
              </ul>
            </div>

            {/* Community */}
            <div className="space-y-4">
              <h4 className="text-sm font-mono text-gray-400 uppercase tracking-wider">Community</h4>
              <ul className="space-y-2 text-sm text-gray-500">
                <li><a href="#" className="hover:text-white transition-colors">GitHub</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Discord</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Status</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-gray-900 pt-8 flex flex-col sm:flex-row items-center justify-between text-sm text-gray-500">
            <div>© 2026 NIYANTA Systems. All rights reserved.</div>
            <div className="flex gap-6 mt-4 sm:mt-0">
              <a href="#" className="hover:text-white transition-colors">Privacy</a>
              <a href="#" className="hover:text-white transition-colors">Terms</a>
              <a href="#" className="hover:text-white transition-colors">Status</a>
            </div>
          </div>
        </div>
      </footer>

      {/* Documentation Modal */}
      {showDocs && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div 
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowDocs(false)}
          ></div>

          {/* Modal Content */}
          <div className="relative bg-gray-900 border border-gray-800 rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto shadow-2xl">
            {/* Header */}
            <div className="sticky top-0 bg-gray-950 border-b border-gray-800 p-6 flex items-center justify-between">
              <h2 className="text-2xl font-bold">Documentation</h2>
              <button
                onClick={() => setShowDocs(false)}
                className="text-gray-400 hover:text-white transition-colors text-2xl leading-none"
              >
                ×
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6 text-gray-300">
              {/* Overview Section */}
              <div className="space-y-3">
                <h3 className="text-xl font-semibold text-cyan-400">Overview</h3>
                <p className="text-sm leading-relaxed">
                  NIYANTA is an advanced Retrieval-Augmented Generation (RAG) system that intelligently routes queries to the most optimal processing pipeline. It combines vector similarity search, graph-based retrieval, and multi-step reasoning for comprehensive information retrieval.
                </p>
              </div>

              {/* Key Features */}
              <div className="space-y-3">
                <h3 className="text-xl font-semibold text-cyan-400">Key Features</h3>
                <ul className="space-y-2 text-sm">
                  <li className="flex gap-3">
                    <span className="text-teal-400">→</span>
                    <span><strong>Intelligent Query Routing:</strong> Automatically detects query complexity and routes to appropriate pipeline</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="text-teal-400">→</span>
                    <span><strong>Hybrid Retrieval:</strong> Combines vector and graph-based search for comprehensive results</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="text-teal-400">→</span>
                    <span><strong>Distributed Processing:</strong> Scalable worker architecture for handling concurrent queries</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="text-teal-400">→</span>
                    <span><strong>Semantic Caching:</strong> Optimizes performance by caching similar queries</span>
                  </li>
                </ul>
              </div>

              {/* System Architecture */}
              <div className="space-y-3">
                <h3 className="text-xl font-semibold text-cyan-400">System Architecture</h3>
                <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 text-sm font-mono space-y-2">
                  <div><span className="text-cyan-400">Frontend:</span> React + Vite + Tailwind</div>
                  <div><span className="text-cyan-400">Backend:</span> FastAPI + LangGraph</div>
                  <div><span className="text-cyan-400">Vector DB:</span> ChromaDB</div>
                  <div><span className="text-cyan-400">Graph DB:</span> Neo4j</div>
                  <div><span className="text-cyan-400">Cache:</span> Redis</div>
                  <div><span className="text-cyan-400">Task Queue:</span> RabbitMQ</div>
                </div>
              </div>

              {/* Processing Modes */}
              <div className="space-y-3">
                <h3 className="text-xl font-semibold text-cyan-400">Processing Modes</h3>
                <div className="space-y-3">
                  <div className="border border-gray-700 rounded-lg p-3">
                    <h4 className="font-semibold text-cyan-300 mb-2">Fast Path (Standard RAG)</h4>
                    <p className="text-xs">Optimized for straightforward queries. Uses direct vector similarity search and instant answer generation. Latency: ~1s</p>
                  </div>
                  <div className="border border-gray-700 rounded-lg p-3">
                    <h4 className="font-semibold text-teal-300 mb-2">Reasoning Path (Agentic RAG)</h4>
                    <p className="text-xs">For complex queries requiring deep analysis. Multi-step reasoning with hybrid retrieval. Latency: ~4-5s</p>
                  </div>
                </div>
              </div>

              {/* Quick Start */}
              <div className="space-y-3">
                <h3 className="text-xl font-semibold text-cyan-400">Quick Start</h3>
                <ol className="space-y-2 text-sm list-decimal list-inside">
                  <li>Click "Sign In" or "Get Started" to begin</li>
                  <li>Create your account (demo: demo/demo123)</li>
                  <li>Enter your query in the dashboard</li>
                  <li>System automatically selects optimal processing path</li>
                  <li>View results with source citations</li>
                </ol>
              </div>

              {/* Support */}
              <div className="space-y-3">
                <h3 className="text-xl font-semibold text-cyan-400">Getting Help</h3>
                <p className="text-sm">
                  For more information, visit our GitHub repository or check the API documentation. Questions? Contact our support team.
                </p>
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-gray-800 p-6 bg-gray-950">
              <button
                onClick={() => setShowDocs(false)}
                className="w-full px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 transition-all duration-300 font-medium text-sm"
              >
                Close Documentation
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes blob {
          0%, 100% {
            transform: translate(0, 0) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
        }

        @keyframes fadeInLeft {
          from {
            opacity: 0;
            transform: translateX(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        @keyframes fadeInRight {
          from {
            opacity: 0;
            transform: translateX(20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        .animate-blob {
          animation: blob 7s infinite;
        }

        .animation-delay-2000 {
          animation-delay: 2s;
        }

        .animation-delay-4000 {
          animation-delay: 4s;
        }

        .animate-fadeInLeft {
          animation: fadeInLeft 1s ease-out forwards;
        }

        .animate-fadeInRight {
          animation: fadeInRight 1s ease-out 0.2s forwards;
          opacity: 0;
        }
      `}</style>
    </div>
  );
}

export default LandingPage;
