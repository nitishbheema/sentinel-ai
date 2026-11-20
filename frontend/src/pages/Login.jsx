import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, Lock, User, Mail, AlertCircle, ArrowRight, CheckCircle2, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

const Login = () => {
  const [isSetupMode, setIsSetupMode] = useState(false);
  const [setupChecking, setSetupChecking] = useState(true);

  // Form fields
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const checkSetupStatus = async () => {
      try {
        const res = await api.get('/auth/setup-status');
        if (res.data?.setup_required) {
          setIsSetupMode(true);
        }
      } catch (err) {
        console.warn('Unable to query setup status:', err);
      } finally {
        setSetupChecking(false);
      }
    };
    checkSetupStatus();
  }, []);

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleSetupSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (password.length < 12) {
      setError('Password must be at least 12 characters long.');
      return;
    }

    setLoading(true);
    try {
      const res = await api.post('/auth/setup-admin', {
        username,
        email,
        password
      });

      // Automatically store tokens and proceed to dashboard
      localStorage.setItem('sentinel_access_token', res.data.access_token);
      localStorage.setItem('sentinel_refresh_token', res.data.refresh_token);
      localStorage.setItem('sentinel_user', JSON.stringify(res.data.user));
      navigate('/');
      window.location.reload();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to initialize administrator account.');
    } finally {
      setLoading(false);
    }
  };

  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasNumber = /\d/.test(password);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>\-_=+]/.test(password);
  const hasMinLen = password.length >= 12;

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
            {isSetupMode ? <ShieldCheck className="w-8 h-8 text-white" /> : <ShieldAlert className="w-8 h-8 text-white" />}
          </div>
          <h1 className="text-2xl font-black tracking-wider text-slate-100 uppercase">
            SENTINEL<span className="text-cyan-400">AI</span>
          </h1>
          <p className="text-xs font-mono text-slate-400 mt-1 uppercase tracking-widest">
            {isSetupMode ? 'First-Time Administrator Setup' : 'Intelligent SOC Platform & Defense Response'}
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

          {isSetupMode ? (
            /* First-Time Setup Form */
            <form onSubmit={handleSetupSubmit} className="space-y-4">
              <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl mb-4 text-xs text-cyan-300">
                Welcome to SentinelAI. Create your root administrator account to initialize the platform.
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5">
                  Admin Username
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
                    placeholder="e.g. secadmin"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5">
                  Admin Email
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-9 pr-3 py-2.5 bg-[#141b2b] border border-[#232f46] rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                    placeholder="admin@yourdomain.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5">
                  Secure Password
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
                    placeholder="Min 12 chars, upper, lower, digit, symbol"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-400 mb-1.5">
                  Confirm Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full pl-9 pr-3 py-2.5 bg-[#141b2b] border border-[#232f46] rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                    placeholder="Repeat password"
                  />
                </div>
              </div>

              {/* Password strength checklist */}
              <div className="p-3 bg-[#111726] border border-[#1b253b] rounded-lg text-[11px] font-mono space-y-1 text-slate-400">
                <div className="text-slate-300 font-semibold mb-1">Password Requirements:</div>
                <div className={`flex items-center gap-1.5 ${hasMinLen ? 'text-emerald-400' : 'text-slate-500'}`}>
                  <span>{hasMinLen ? '✓' : '○'}</span> At least 12 characters
                </div>
                <div className={`flex items-center gap-1.5 ${hasUpper && hasLower ? 'text-emerald-400' : 'text-slate-500'}`}>
                  <span>{hasUpper && hasLower ? '✓' : '○'}</span> Uppercase and lowercase letters
                </div>
                <div className={`flex items-center gap-1.5 ${hasNumber ? 'text-emerald-400' : 'text-slate-500'}`}>
                  <span>{hasNumber ? '✓' : '○'}</span> At least one number
                </div>
                <div className={`flex items-center gap-1.5 ${hasSpecial ? 'text-emerald-400' : 'text-slate-500'}`}>
                  <span>{hasSpecial ? '✓' : '○'}</span> At least one special symbol
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || !hasMinLen || !hasUpper || !hasLower || !hasNumber || !hasSpecial}
                className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 text-slate-900 font-bold text-sm rounded-lg shadow-lg shadow-emerald-600/30 transition flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
              >
                {loading ? <span>Initializing System...</span> : <span>Initialize Administrator</span>}
              </button>
            </form>
          ) : (
            /* Standard Login Form */
            <form onSubmit={handleLoginSubmit} className="space-y-4">
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
                    placeholder="Enter username"
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
          )}
        </div>

        <div className="text-center mt-6">
          <p className="text-xs font-mono text-slate-500">
            Encrypted with Argon2id • RBAC Enforced • Zero Insecure Defaults
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
