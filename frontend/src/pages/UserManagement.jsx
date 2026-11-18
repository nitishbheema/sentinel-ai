import React, { useState, useEffect } from 'react';
import { Users, Plus, Shield, Check, X, Lock } from 'lucide-react';
import api from '../services/api';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('ANALYST');

  const fetchUsers = async () => {
    try {
      const res = await api.get('/auth/users');
      setUsers(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await api.post('/auth/users', {
        username,
        email,
        password,
        role,
        is_active: true,
      });
      setShowModal(false);
      setUsername('');
      setEmail('');
      setPassword('');
      fetchUsers();
    } catch (err) {
      console.error('Error creating user:', err);
    }
  };

  const toggleUserActive = async (user) => {
    try {
      await api.patch(`/auth/users/${user.id}`, {
        is_active: !user.is_active,
      });
      fetchUsers();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#162032]">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Users className="w-5 h-5 text-cyan-400" />
            <span>Role-Based User Administration</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Manage platform analyst accounts, role authorizations (Admin, Analyst, Viewer), and lockout states
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-3.5 py-2 bg-cyan-600 hover:bg-cyan-500 text-slate-900 font-bold text-xs rounded-lg shadow-lg shadow-cyan-600/30 transition flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          <span>Provision New User</span>
        </button>
      </div>

      {/* Users Table */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl overflow-hidden shadow-lg">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#162032] text-slate-400 border-b border-[#1f293d]">
            <tr>
              <th className="py-3 px-4">User ID</th>
              <th className="py-3 px-4">Username</th>
              <th className="py-3 px-4">Email Address</th>
              <th className="py-3 px-4">RBAC Role</th>
              <th className="py-3 px-4">Failed Logins</th>
              <th className="py-3 px-4">Account Status</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#182335] text-slate-300">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-[#141d2d] transition">
                <td className="py-3 px-4 font-bold text-cyan-400">#{u.id}</td>
                <td className="py-3 px-4 font-bold text-slate-100">@{u.username}</td>
                <td className="py-3 px-4 text-slate-400">{u.email}</td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    u.role === 'ADMIN' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                    u.role === 'ANALYST' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' :
                    'bg-slate-700/30 text-slate-400'
                  }`}>
                    {u.role}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <span className={u.failed_login_attempts > 0 ? 'text-orange-400 font-bold' : 'text-slate-500'}>
                    {u.failed_login_attempts} / 5
                  </span>
                </td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    u.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                  }`}>
                    {u.is_active ? 'ACTIVE' : 'DEACTIVATED'}
                  </span>
                </td>
                <td className="py-3 px-4 text-right">
                  <button
                    onClick={() => toggleUserActive(u)}
                    className="px-2.5 py-1 rounded bg-[#162032] border border-[#233149] text-slate-300 hover:text-cyan-400 transition"
                  >
                    {u.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/75 flex items-center justify-center p-4 z-50">
          <div className="bg-[#0e1422] border border-[#223049] rounded-2xl max-w-md w-full p-6 shadow-2xl font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-[#1f293d] mb-4">
              <h2 className="text-sm font-bold text-slate-100">Provision Platform Analyst</h2>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-slate-400 mb-1">Username</label>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-[#162032] border border-[#223049] rounded-lg p-2.5 text-slate-100"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-[#162032] border border-[#223049] rounded-lg p-2.5 text-slate-100"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Passphrase (min 8 chars)</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-[#162032] border border-[#223049] rounded-lg p-2.5 text-slate-100"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">RBAC Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full bg-[#162032] border border-[#223049] rounded-lg p-2.5 text-slate-100"
                >
                  <option value="ANALYST">ANALYST (Triage, Alerts, Incidents)</option>
                  <option value="ADMIN">ADMIN (Full Platform Privileges)</option>
                  <option value="VIEWER">VIEWER (Read-Only Dashboards)</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#1f293d]">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 rounded bg-[#162032] text-slate-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-slate-900 font-bold"
                >
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
