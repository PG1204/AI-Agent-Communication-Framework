'use client';
import { useState, useEffect } from 'react';
import { ArrowRight, Bot, Cpu, Network, Zap, Shield, Globe, Moon, Sun } from 'lucide-react';
import Link from 'next/link';

export default function LandingPage() {
  const [isHovered, setIsHovered] = useState(false);
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    // Load theme from localStorage on mount
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
      setIsDark(false);
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
  };

  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      isDark 
        ? 'bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900' 
        : 'bg-gradient-to-br from-slate-50 via-purple-50 to-slate-50'
    }`}>
      {/* Navigation */}
      <nav className={`fixed top-0 w-full backdrop-blur-md border-b z-50 transition-colors ${
        isDark 
          ? 'bg-black/10 border-white/10' 
          : 'bg-white/80 border-slate-200'
      }`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-2">
              <Network className={`h-8 w-8 ${isDark ? 'text-purple-400' : 'text-purple-600'}`} />
              <span className={`text-xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>AgentFlow</span>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={toggleTheme}
                className={`p-2 rounded-lg transition-colors border ${
                  isDark 
                    ? 'bg-slate-700/50 hover:bg-slate-600 border-slate-600' 
                    : 'bg-white hover:bg-slate-100 border-slate-300'
                }`}
                aria-label="Toggle theme"
              >
                {isDark ? (
                  <Sun className="h-5 w-5 text-yellow-400" />
                ) : (
                  <Moon className="h-5 w-5 text-slate-700" />
                )}
              </button>
              <Link href="/chat">
                <button className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors">
                  Launch Platform
                </button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className={`inline-flex items-center px-4 py-2 rounded-full border mb-8 ${
            isDark 
              ? 'bg-purple-500/10 border-purple-500/20' 
              : 'bg-purple-100 border-purple-200'
          }`}>
            <Zap className={`h-4 w-4 mr-2 ${isDark ? 'text-purple-400' : 'text-purple-600'}`} />
            <span className={`text-sm ${isDark ? 'text-purple-300' : 'text-purple-700'}`}>
              Multi-Agent AI Communication Framework
            </span>
          </div>
          
          <h1 className={`text-5xl md:text-7xl font-bold mb-6 ${isDark ? 'text-white' : 'text-slate-900'}`}>
            The Future of
            <span className="block bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              AI Collaboration
            </span>
          </h1>
          
          <p className={`text-xl mb-12 max-w-3xl mx-auto leading-relaxed ${
            isDark ? 'text-gray-300' : 'text-slate-600'
          }`}>
            Build intelligent systems where specialized AI agents communicate, coordinate, 
            and collaborate in real-time to solve complex problems.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link href="/chat">
              <button 
                className={`px-8 py-4 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-semibold text-lg transition-all duration-300 flex items-center ${isHovered ? 'scale-105' : ''}`}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
              >
                Try Live Demo
                <ArrowRight className="ml-2 h-5 w-5" />
              </button>
            </Link>
            <button className={`px-8 py-4 border rounded-xl font-semibold text-lg transition-all ${
              isDark 
                ? 'border-white/20 text-white hover:bg-white/5' 
                : 'border-slate-300 text-slate-900 hover:bg-slate-100'
            }`}>
              Watch Demo Video
            </button>
          </div>

          {/* Demo Preview */}
          <div className="relative max-w-5xl mx-auto">
            <div className="absolute -inset-4 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-3xl blur-2xl"></div>
            <div className={`relative backdrop-blur-xl rounded-2xl border p-8 ${
              isDark 
                ? 'bg-slate-800/50 border-white/10' 
                : 'bg-white/90 border-slate-200'
            }`}>
              <div className="grid md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="inline-flex p-4 bg-blue-500/10 rounded-2xl mb-4">
                    <Bot className={`h-8 w-8 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
                  </div>
                  <h3 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                    Research Agent
                  </h3>
                  <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-slate-600'}`}>
                    Gathers technical insights and recommendations
                  </p>
                </div>
                <div className="text-center">
                  <div className="inline-flex p-4 bg-green-500/10 rounded-2xl mb-4">
                    <Cpu className={`h-8 w-8 ${isDark ? 'text-green-400' : 'text-green-600'}`} />
                  </div>
                  <h3 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                    Code Agent
                  </h3>
                  <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-slate-600'}`}>
                    Writes and debugs production-ready code
                  </p>
                </div>
                <div className="text-center">
                  <div className="inline-flex p-4 bg-purple-500/10 rounded-2xl mb-4">
                    <Network className={`h-8 w-8 ${isDark ? 'text-purple-400' : 'text-purple-600'}`} />
                  </div>
                  <h3 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                    Coordinator
                  </h3>
                  <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-slate-600'}`}>
                    Orchestrates complex multi-agent workflows
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className={`py-20 px-4 sm:px-6 lg:px-8 ${
        isDark ? 'bg-black/20' : 'bg-slate-100/50'
      }`}>
        <div className="max-w-7xl mx-auto">
          <h2 className={`text-3xl md:text-4xl font-bold text-center mb-16 ${
            isDark ? 'text-white' : 'text-slate-900'
          }`}>
            Built for the Enterprise
          </h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className={`backdrop-blur-sm rounded-2xl p-6 border ${
              isDark 
                ? 'bg-slate-800/30 border-white/5' 
                : 'bg-white border-slate-200'
            }`}>
              <Shield className="h-10 w-10 text-green-400 mb-4" />
              <h3 className={`text-xl font-semibold mb-3 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                Enterprise Security
              </h3>
              <p className={isDark ? 'text-gray-400' : 'text-slate-600'}>
                JWT authentication, rate limiting, and secure agent communication protocols.
              </p>
            </div>
            
            <div className={`backdrop-blur-sm rounded-2xl p-6 border ${
              isDark 
                ? 'bg-slate-800/30 border-white/5' 
                : 'bg-white border-slate-200'
            }`}>
              <Zap className="h-10 w-10 text-yellow-400 mb-4" />
              <h3 className={`text-xl font-semibold mb-3 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                Real-time Performance
              </h3>
              <p className={isDark ? 'text-gray-400' : 'text-slate-600'}>
                gRPC streaming for instant agent communication with sub-100ms latency.
              </p>
            </div>
            
            <div className={`backdrop-blur-sm rounded-2xl p-6 border ${
              isDark 
                ? 'bg-slate-800/30 border-white/5' 
                : 'bg-white border-slate-200'
            }`}>
              <Globe className="h-10 w-10 text-blue-400 mb-4" />
              <h3 className={`text-xl font-semibold mb-3 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                Scalable Architecture
              </h3>
              <p className={isDark ? 'text-gray-400' : 'text-slate-600'}>
                Microservices design that scales from prototype to production workloads.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className={`text-3xl md:text-4xl font-bold mb-6 ${isDark ? 'text-white' : 'text-slate-900'}`}>
            Ready to Build the Future?
          </h2>
          <p className={`text-xl mb-8 ${isDark ? 'text-gray-300' : 'text-slate-600'}`}>
            Join the next generation of AI-powered applications.
          </p>
          <Link href="/chat">
            <button className="px-10 py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-semibold text-lg hover:scale-105 transition-transform">
              Start Building Now
            </button>
          </Link>
        </div>
      </section>
    </div>
  );
}
