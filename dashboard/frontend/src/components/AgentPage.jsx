import React, { useState, useMemo, useEffect } from "react";
import { Search, Filter, ArrowUpDown, MoreVertical, Trash2, Edit2, Monitor, Shield, Server, Globe, Wifi, WifiOff } from "lucide-react";

export default function AgentPage({
    agents,
    setSelectedAgent,
    fetchAgentDetails,
    setShowAddAgent,
    lastSync,
    connectionOk = true
}) {
    const [searchTerm, setSearchText] = useState("");
    const [statusFilter, setStatusFilter] = useState("All");
    const [osFilter, setOsFilter] = useState("All");
    const [sortConfig, setSortConfig] = useState({ key: 'hostname', direction: 'asc' });

    // Ticks once a second just to force the "Updated Xs ago" label to
    // re-render - it doesn't refetch anything itself.
    const [, forceTick] = useState(0);
    useEffect(() => {
        const t = setInterval(() => forceTick(x => x + 1), 1000);
        return () => clearInterval(t);
    }, []);

    const filteredAgents = useMemo(() => {
        let result = [...agents];

        // Search - supports Agent ID (numeric), hostname, name, IP, OS, group.
        if (searchTerm) {
            const term = searchTerm.toLowerCase().trim();
            result = result.filter(a =>
                String(a.id).includes(term) ||
                (a.hostname?.toLowerCase().includes(term)) ||
                (a.name?.toLowerCase().includes(term)) ||
                (a.ip_address?.toLowerCase().includes(term)) ||
                (a.operating_system?.toLowerCase().includes(term)) ||
                (a.agent_group?.toLowerCase().includes(term))
            );
        }

        // Status Filter
        if (statusFilter !== "All") {
            result = result.filter(a => a.status === statusFilter);
        }

        // OS Filter
        if (osFilter !== "All") {
            result = result.filter(a => a.operating_system?.includes(osFilter));
        }

        // Sort
        result.sort((a, b) => {
            const valA = a[sortConfig.key] || "";
            const valB = b[sortConfig.key] || "";
            if (valA < valB) return sortConfig.direction === 'asc' ? -1 : 1;
            if (valA > valB) return sortConfig.direction === 'asc' ? 1 : -1;
            return 0;
        });

        return result;
    }, [agents, searchTerm, statusFilter, osFilter, sortConfig]);

    const requestSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const statusColors = {
        Active: "bg-emerald-100 text-emerald-700 border-emerald-200",
        Online: "bg-emerald-100 text-emerald-700 border-emerald-200",
        Pending: "bg-amber-100 text-amber-700 border-amber-200",
        Connecting: "bg-blue-100 text-blue-700 border-blue-200",
        Offline: "bg-slate-100 text-slate-600 border-slate-200",
        Disconnected: "bg-rose-100 text-rose-700 border-rose-200"
    };

    const secondsAgo = lastSync ? Math.max(0, Math.floor((Date.now() - lastSync.getTime()) / 1000)) : null;
    const counts = useMemo(() => ({
        active: agents.filter(a => a.status === 'Active' || a.status === 'Online').length,
        pending: agents.filter(a => a.status === 'Pending' || a.status === 'Connecting').length,
        offline: agents.filter(a => a.status === 'Offline' || a.status === 'Disconnected').length,
    }), [agents]);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Agent Management</h1>
                    <p className="text-slate-500 mt-1">Monitor and manage enrolled endpoints across the enterprise</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className={`flex items-center gap-1.5 text-xs font-semibold ${connectionOk ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {connectionOk ? <Wifi size={14} /> : <WifiOff size={14} />}
                        {connectionOk
                            ? (secondsAgo !== null ? `Live · updated ${secondsAgo}s ago` : 'Live')
                            : 'Reconnecting…'}
                    </div>
                    <button
                        onClick={() => setShowAddAgent(true)}
                        className="px-6 py-3 rounded-xl bg-indigo-600 text-white font-bold text-sm shadow-lg shadow-indigo-500/25 hover:bg-indigo-700 transition-all flex items-center gap-2"
                    >
                        <span>+</span> Enroll New Agent
                    </button>
                </div>
            </div>

            {/* Filters Bar */}
            <div className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl p-4 shadow-sm flex flex-wrap gap-4 items-center">
                <div className="relative flex-1 min-w-[300px]">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                    <input
                        type="text"
                        placeholder="Search by Agent ID, hostname, name, IP, OS or group..."
                        value={searchTerm}
                        onChange={(e) => setSearchText(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                    />
                </div>

                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                        <Filter size={14} className="text-slate-400" />
                        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Status:</span>
                    </div>
                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-semibold focus:outline-none focus:border-indigo-500"
                    >
                        <option>All</option>
                        <option>Active</option>
                        <option>Pending</option>
                        <option>Connecting</option>
                        <option>Offline</option>
                        <option>Disconnected</option>
                    </select>
                </div>

                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                        <Monitor size={14} className="text-slate-400" />
                        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">OS:</span>
                    </div>
                    <select
                        value={osFilter}
                        onChange={(e) => setOsFilter(e.target.value)}
                        className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-semibold focus:outline-none focus:border-indigo-500"
                    >
                        <option>All</option>
                        <option>Windows</option>
                        <option>Linux</option>
                        <option>Ubuntu</option>
                    </select>
                </div>
            </div>

            {/* Agents Table */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200/60 overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-slate-50/50 border-b border-slate-100">
                            <th className="p-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest cursor-pointer hover:text-indigo-600 transition-colors" onClick={() => requestSort('hostname')}>
                                <div className="flex items-center gap-2">Agent / Hostname <ArrowUpDown size={12} /></div>
                            </th>
                            <th className="p-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest cursor-pointer hover:text-indigo-600 transition-colors" onClick={() => requestSort('operating_system')}>
                                <div className="flex items-center gap-2">Operating System <ArrowUpDown size={12} /></div>
                            </th>
                            <th className="p-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest cursor-pointer hover:text-indigo-600 transition-colors" onClick={() => requestSort('ip_address')}>
                                <div className="flex items-center gap-2">IP Address <ArrowUpDown size={12} /></div>
                            </th>
                            <th className="p-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest cursor-pointer hover:text-indigo-600 transition-colors" onClick={() => requestSort('agent_group')}>
                                <div className="flex items-center gap-2">Group <ArrowUpDown size={12} /></div>
                            </th>
                            <th className="p-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest cursor-pointer hover:text-indigo-600 transition-colors" onClick={() => requestSort('status')}>
                                <div className="flex items-center gap-2">Status <ArrowUpDown size={12} /></div>
                            </th>
                            <th className="p-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredAgents.length === 0 ? (
                            <tr>
                                <td colSpan={6} className="py-20 text-center">
                                    <div className="flex flex-col items-center gap-3">
                                        <div className="w-12 h-12 rounded-full bg-slate-50 flex items-center justify-center">
                                            <Shield size={24} className="text-slate-300" />
                                        </div>
                                        <p className="text-slate-400 font-medium">No agents found matching your criteria</p>
                                        <button onClick={() => {setSearchText(""); setStatusFilter("All"); setOsFilter("All");}} className="text-xs font-bold text-indigo-600 hover:underline">Clear all filters</button>
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            filteredAgents.map(agent => (
                                <tr
                                    key={agent.id}
                                    onClick={() => {
                                        setSelectedAgent(agent);
                                        fetchAgentDetails(agent.id);
                                    }}
                                    className="border-b border-slate-50 hover:bg-indigo-50/30 transition-colors cursor-pointer group"
                                >
                                    <td className="p-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center group-hover:bg-white transition-colors shadow-sm">
                                                <Server size={16} className="text-slate-500" />
                                            </div>
                                            <div>
                                                <div className="font-bold text-slate-900 text-sm">{agent.name || agent.hostname || `Agent #${agent.id}`}</div>
                                                <div className="text-[10px] font-mono text-slate-400 uppercase tracking-tight">{agent.hostname || "Pending..."}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <span className="text-xs font-semibold text-slate-700">{agent.operating_system || "—"}</span>
                                            {agent.os_version && <span className="text-[10px] text-slate-400">({agent.os_version})</span>}
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-1.5 font-mono text-xs text-slate-600">
                                            <Globe size={12} className="text-slate-300" />
                                            {agent.ip_address || "—"}
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <span className="px-2 py-1 rounded-md bg-slate-100 text-slate-600 text-[10px] font-bold border border-slate-200 uppercase tracking-wider">
                                            {agent.agent_group || "Default"}
                                        </span>
                                    </td>
                                    <td className="p-4">
                                        <span className={`px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider border flex items-center gap-1.5 w-fit ${statusColors[agent.status] || statusColors.Offline}`}>
                                            <span className={`w-1.5 h-1.5 rounded-full ${agent.status === 'Active' ? 'bg-emerald-500 animate-pulse' : 'bg-current opacity-60'}`}></span>
                                            {agent.status}
                                        </span>
                                    </td>
                                    <td className="p-4 text-right">
                                        <button className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all">
                                            <MoreVertical size={16} />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            <div className="flex justify-between items-center text-xs text-slate-500 font-medium px-2">
                <div>Showing {filteredAgents.length} of {agents.length} enrolled agents</div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-emerald-500"></div> Active ({counts.active})</div>
                    <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-amber-500"></div> Pending ({counts.pending})</div>
                    <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-slate-400"></div> Offline ({counts.offline})</div>
                </div>
            </div>
        </div>
    );
}
