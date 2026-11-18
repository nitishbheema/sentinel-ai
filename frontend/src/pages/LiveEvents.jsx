import React, { useState, useEffect } from 'react';
import { Radio, Search, Filter, RefreshCw, Eye, X, Terminal } from 'lucide-react';
import api from '../services/api';

const LiveEvents = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sourceFilter, setSourceFilter] = useState('');
  const [search, setSearch] = useState('');
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [page, setPage] = useState(0);

  const fetchEvents = async () => {
    try {
      let url = `/events?skip=${page * 50}&limit=50`;
      if (sourceFilter) url += `&event_source=${sourceFilter}`;
      const res = await api.get(url);
      setEvents(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 5000);
    return () => clearInterval(interval);
  }, [sourceFilter, page]);

  const filteredEvents = events.filter((e) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      e.event_type?.toLowerCase().includes(q) ||
      e.source_ip?.toLowerCase().includes(q) ||
      e.destination_ip?.toLowerCase().includes(q) ||
      e.host_id?.toLowerCase().includes(q) ||
      e.username?.toLowerCase().includes(q) ||
      e.process_name?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#162032]">
        <div>
          <h1 className="text-xl font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Radio className="w-5 h-5 text-cyan-400" />
            <span>Live Security Events Feed</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Normalized telemetry from Zeek network sensors, Suricata IDS, and Linux/Windows endpoint agents
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchEvents}
            className="px-3 py-1.5 rounded-lg bg-[#111827] border border-[#1f293d] hover:border-cyan-500/50 text-slate-300 text-xs font-mono flex items-center gap-2 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Poll Stream</span>
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col md:flex-row items-center gap-4 bg-[#111827] border border-[#1f293d] p-4 rounded-xl shadow-lg">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search IP, port, host, user, process..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-[#162032] border border-[#223049] rounded-lg pl-9 pr-4 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <span className="text-xs font-mono text-slate-400">Source:</span>
          {['', 'zeek', 'suricata', 'endpoint'].map((src) => (
            <button
              key={src}
              onClick={() => { setSourceFilter(src); setPage(0); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition ${
                sourceFilter === src
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                  : 'bg-[#162032] text-slate-400 hover:text-slate-200 border border-[#223049]'
              }`}
            >
              {src ? src.toUpperCase() : 'ALL'}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#111827] border border-[#1f293d] rounded-xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#162032] text-slate-400 border-b border-[#1f293d]">
              <tr>
                <th className="py-3 px-4">Time (UTC)</th>
                <th className="py-3 px-4">Source</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Flow (Src → Dst)</th>
                <th className="py-3 px-4">Host / Entity</th>
                <th className="py-3 px-4">Process / User</th>
                <th className="py-3 px-4 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#182335] text-slate-300">
              {filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-slate-500 font-mono">
                    No telemetry events matched the active filters
                  </td>
                </tr>
              ) : (
                filteredEvents.map((ev) => (
                  <tr key={ev.id} className="hover:bg-[#141d2d] transition">
                    <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                      {new Date(ev.timestamp || ev.created_at).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        ev.event_source === 'suricata' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                        ev.event_source === 'zeek' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                        'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                      }`}>
                        {ev.event_source.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-200 font-semibold">{ev.event_type}</td>
                    <td className="py-3 px-4 text-slate-300">
                      {ev.source_ip ? (
                        <span>
                          <strong className="text-slate-100">{ev.source_ip}</strong>
                          {ev.source_port ? `:${ev.source_port}` : ''} →{' '}
                          <strong className="text-cyan-400">{ev.destination_ip || 'local'}</strong>
                          {ev.destination_port ? `:${ev.destination_port}` : ''}
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-300">{ev.host_id || 'network'}</td>
                    <td className="py-3 px-4">
                      {ev.process_name ? (
                        <span className="text-cyan-400">{ev.process_name} (PID: {ev.process_pid})</span>
                      ) : ev.username ? (
                        <span className="text-slate-300">{ev.username}</span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setSelectedEvent(ev)}
                        className="p-1 rounded hover:bg-[#1f293d] text-cyan-400 hover:text-cyan-300 transition"
                        title="Inspect Raw Event"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination controls */}
        <div className="flex items-center justify-between p-4 border-t border-[#1f293d] text-xs font-mono text-slate-400 bg-[#0e1422]">
          <span>Page {page + 1}</span>
          <div className="flex items-center gap-2">
            <button
              disabled={page === 0}
              onClick={() => setPage(p => Math.max(0, p - 1))}
              className="px-3 py-1 rounded bg-[#162032] border border-[#223049] hover:bg-[#1a253a] disabled:opacity-40 transition"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => p + 1)}
              className="px-3 py-1 rounded bg-[#162032] border border-[#223049] hover:bg-[#1a253a] transition"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* JSON Inspector Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-[#0e1422] border border-[#223049] rounded-xl max-w-2xl w-full max-h-[80vh] flex flex-col shadow-2xl">
            <div className="p-4 border-b border-[#1f293d] flex items-center justify-between">
              <div className="flex items-center gap-2 text-cyan-400 font-mono text-sm font-bold">
                <Terminal className="w-4 h-4" />
                <span>Event Inspector: {selectedEvent.event_uuid}</span>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto font-mono text-xs text-slate-300 bg-[#080c14]">
              <pre>{JSON.stringify(selectedEvent, null, 2)}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveEvents;
