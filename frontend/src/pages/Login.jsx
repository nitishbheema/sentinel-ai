import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, Lock, User, Key, AlertCircle, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Login = () => {
  const [username, setUsername] = useState('analyst');
  const [password, setPassword] = useState('SentinelAnalyst2026!');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  const setRoleAccount = (u, p) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#070a10] px-4 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-20 pointer-events-none" />
      <div className="absolute -top-40 -right-40 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-md w-full z-10">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan-600 to-blue-500 mb-4 shadow-xl shadow-cyan-500/20">
            <ShieldAlert className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-black tracking-wider text-slate-100 uppercase">
            SENTINEL<span className="text-cyan-400">AI</span>
          </h1>
          <p className="text-xs font-mono text-slate-400 mt-1 uppercase tracking-widest">
            Intelligent SOC Platform & Defense Response
          </p>
        </div>

        {/* Card */}
        <div className="bg-[#0e1422] border border-[#1d273b] rounded-2xl p-8 shadow-2xl">
          {error && (
            <div className="mb-6 p-3 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center gap-2 text-red-400 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5">
                Username / Call-Sign
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 bg-[#141b2b] border border-[#232f46] rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                  placeholder="analyst"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5">
                Passphrase
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 bg-[#141b2b] border border-[#232f46] rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                  placeholder="••••••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-cyan-600 hover:bg-cyan-500 text-slate-900 font-bold text-sm rounded-lg shadow-lg shadow-cyan-600/30 transition flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
            >
              {loading ? (
                <span>Authenticating...</span>
              ) : (
                <>
                  <span>Sign In to SOC Console</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Role Fillers */}
          <div className="mt-6 pt-6 border-t border-[#1a2333]">
            <p className="text-[11px] font-mono text-slate-400 mb-2.5 uppercase tracking-wider text-center">
              Quick Role Switch (Lab Demo):
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setRoleAccount('admin', 'SentinelAdmin2026!')}
                className="py-1.5 px-2 bg-[#141c2c] hover:bg-[#1a253a] border border-[#233048] rounded text-[11px] font-mono text-slate-300 transition text-center"
              >
                ADMIN
              </button>
              <button
                type="button"
                onClick={() => setRoleAccount('analyst', 'SentinelAnalyst2026!')}
                className="py-1.5 px-2 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 rounded text-[11px] font-mono text-cyan-400 transition text-center"
              >
                ANALYST
              </button>
              <button
                type="button"
                onClick={() => setRoleAccount('viewer', 'SentinelViewer2026!')}
                className="py-1.5 px-2 bg-[#141c2c] hover:bg-[#1a253a] border border-[#233048] rounded text-[11px] font-mono text-slate-300 transition text-center"
              >
                VIEWER
              </button>
            </div>
          </div>
        </div>

        <div className="text-center mt-6">
          <p className="text-xs font-mono text-slate-500">
            Encrypted with Argon2 • RBAC Enforced • ISO 27001 Compliant
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
