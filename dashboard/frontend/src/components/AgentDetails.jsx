import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Monitor, Cpu, HardDrive, MemoryStick, Activity, ShieldCheck,
  ArrowLeft, Clock, Network, Server, Globe, Fingerprint,
  Calendar, RefreshCw, CheckCircle2, Trash2, Edit2, X, User, Cpu as ArchitectureIcon, Hash
} from "lucide-react";
import AgentLogs from "./AgentLogs";

const pageVariants = {
  initial: { opacity: 0, y: 15 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1], staggerChildren: 0.05 } }
};

export default function AgentDetails({
  agentDetails,
  setSelectedAgent,
  setAgentDetails,
  handleDeleteAgent,
  handleUpdateAgent,
  lastSync,
  connectionOk = true
}) {
  const [showEditModal, setShowEditModal] = useState(false);
  const [editData, setEditData] = useState({});

  const agent = agentDetails || {};

  // Compute health status from usage values
  const cpuUsage = agent.cpu_usage ?? 0;
  const memUsage = agent.memory_usage ?? 0;
  const diskUsage = agent.disk_usage ?? 0;
  const netUsage = agent.network_usage ?? 0;

  const getHealthStatus = (usage) => {
    if (usage >= 90) return { label: "Critical", color: "text-rose-600", bg: "bg-rose-50", border: "border-rose-200" };
    if (usage >= 70) return { label: "Warning", color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200" };
    return { label: "Healthy", color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-200" };
  };

  const cpuHealth = getHealthStatus(cpuUsage);
  const memHealth = getHealthStatus(memUsage);
  const diskHealth = getHealthStatus(diskUsage);
  const netHealth = getHealthStatus(netUsage);

  const agentStatus = agent.status || "Pending";
  const statusConfig = {
    Active: { color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-200", dot: "bg-emerald-500" },
    Connecting: { color: "text-blue-600", bg: "bg-blue-50", border: "border-blue-200", dot: "bg-blue-500" },
    Online: { color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-200", dot: "bg-emerald-500" },
    Offline: { color: "text-slate-500", bg: "bg-slate-50", border: "border-slate-200", dot: "bg-slate-400" },
    Disconnected: { color: "text-rose-500", bg: "bg-rose-50", border: "border-rose-200", dot: "bg-rose-400" },
    Pending: { color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200", dot: "bg-amber-500" }
  };
  const st = statusConfig[agentStatus] || statusConfig.Pending;

  const formatTime = (t) => {
    if (!t) return "—";
    const d = new Date(t);
    return d.toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
  };

  const lastSeen = agent.last_seen ? new Date(agent.last_seen) : null;
  const heartbeatText = lastSeen ? (() => {
    const secondsAgo = Math.floor((Date.now() - lastSeen.getTime()) / 1000);
    return secondsAgo < 60 ? `${secondsAgo}s ago` : secondsAgo < 3600 ? `${Math.floor(secondsAgo / 60)}m ago` : `${Math.floor(secondsAgo / 3600)}h ago`;
  })() : "Never";

  const openEditModal = () => {
    setEditData({
      agent_group: agent.agent_group || "Default",
      environment: agent.environment || "Production",
      department: agent.department || "",
      description: agent.description || "",
      tags: agent.tags || "",
      owner: agent.owner || ""
    });
    setShowEditModal(true);
  };

  const onUpdateSubmit = (e) => {
    e.preventDefault();
    handleUpdateAgent(agent.id, editData);
    setShowEditModal(false);
  };

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex justify-between items-center">
        <button
          onClick={() => {
            setSelectedAgent(null);
            setAgentDetails(null);
          }}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white border border-slate-200/60 text-slate-700 text-sm font-semibold hover:border-indigo-300 hover:text-indigo-700 hover:shadow-md transition-all shadow-sm"
        >
          <ArrowLeft size={16} />
          Back to Agents
        </button>

        <div className={`flex items-center gap-1.5 text-xs font-semibold ${connectionOk ? 'text-emerald-600' : 'text-rose-600'}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${connectionOk ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`}></span>
          {connectionOk ? 'Live · refreshing every 5s' : 'Reconnecting…'}
        </div>

        <div className="flex items-center gap-3">
            <button
                onClick={openEditModal}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-600 text-sm font-bold hover:bg-slate-50 transition-all"
            >
                <Edit2 size={14} /> Edit
            </button>
            <button
                onClick={() => handleDeleteAgent(agent.id)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-rose-50 border border-rose-100 text-rose-600 text-sm font-bold hover:bg-rose-100 transition-all"
            >
                <Trash2 size={14} /> Delete
            </button>
        </div>
      </div>

      {/* Agent Header */}
      <div className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Monitor className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">{agent.name || agent.hostname || `Agent #${agent.id}`}</h1>
              <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
                <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-[10px]">ID: {agent.id}</span>
                <span className="text-slate-300">|</span>
                <span className="font-medium">{agent.hostname || "Pending Connection..."}</span>
                <span className="text-slate-300">|</span>
                <span>{agent.operating_system || "—"}</span>
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider border ${st.border} ${st.bg} ${st.color} flex items-center gap-2`}>
              <span className={`w-2 h-2 rounded-full ${st.dot} ${agentStatus === "Active" ? "animate-pulse" : ""}`}></span>
              {agentStatus}
            </span>
          </div>
        </div>
      </div>

      {/* Main Info Grid */}
      <div className="grid grid-cols-4 gap-4">
        <InfoCard icon={<Server size={16} />} label="Hostname" value={agent.hostname || "—"} mono />
        <InfoCard icon={<Globe size={16} />} label="IP Address" value={agent.ip_address || "—"} mono />
        <InfoCard icon={<Hash size={16} />} label="MAC Address" value={agent.mac_address || "—"} mono small />
        <InfoCard icon={<Monitor size={16} />} label="OS Version" value={agent.os_version || agent.operating_system || "—"} />

        <InfoCard icon={<ArchitectureIcon size={16} />} label="Architecture" value={agent.architecture || "—"} mono />
        <InfoCard icon={<User size={16} />} label="Current User" value={agent.current_user || "—"} />
        <InfoCard icon={<ShieldCheck size={16} />} label="Agent Version" value={agent.version || "—"} mono />
        <InfoCard icon={<Clock size={16} />} label="Uptime" value={agent.uptime || "—"} />

        <InfoCard icon={<Calendar size={16} />} label="Enrolled" value={formatTime(agent.created_at)} />
        <InfoCard icon={<RefreshCw size={16} />} label="Last Seen" value={formatTime(agent.last_seen)} />
        <InfoCard icon={<Activity size={16} />} label="Heartbeat" value={heartbeatText} />
        <InfoCard icon={<Activity size={16} />} label="Health" value={diskHealth.label} color={diskHealth.color} />
      </div>

      {/* Enterprise Metadata */}
      <div className="grid grid-cols-4 gap-4">
        <InfoCard label="Group" value={agent.agent_group || "Default"} color="text-indigo-600" />
        <InfoCard label="Environment" value={agent.environment || "Production"} color="text-amber-600" />
        <InfoCard label="Department" value={agent.department || "—"} />
        <InfoCard label="Owner" value={agent.owner || "—"} />
      </div>

      {/* Description & Tags */}
      {(agent.description || agent.tags) && (
        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2 bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl p-5 shadow-sm">
            <div className="text-[10px] font-bold tracking-widest text-slate-400 uppercase mb-2">Description</div>
            <div className="text-sm text-slate-600 leading-relaxed">{agent.description || "No description provided."}</div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl p-5 shadow-sm">
            <div className="text-[10px] font-bold tracking-widest text-slate-400 uppercase mb-2">Tags</div>
            <div className="flex flex-wrap gap-2">
              {agent.tags ? agent.tags.split(',').map(tag => (
                <span key={tag} className="px-2 py-1 bg-indigo-50 text-indigo-600 text-[10px] font-bold rounded-md border border-indigo-100">{tag.trim()}</span>
              )) : <span className="text-xs text-slate-400 italic">No tags</span>}
            </div>
          </div>
        </div>
      )}

      {/* Health Metrics */}
      <div className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center">
            <Activity size={16} className="text-indigo-600" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-sm tracking-tight">System Health</h3>
            <p className="text-[10px] text-slate-400 font-medium tracking-wider uppercase">Real-time utilization metrics from endpoint</p>
          </div>
        </div>
        <div className="grid grid-cols-4 gap-4">
          <HealthGauge label="CPU Usage" value={cpuUsage} icon={<Cpu size={14} />} color="indigo" health={cpuHealth} />
          <HealthGauge label="RAM Usage" value={memUsage} icon={<MemoryStick size={14} />} color="violet" health={memHealth} />
          <HealthGauge label="Disk Usage" value={diskUsage} icon={<HardDrive size={14} />} color="amber" health={diskHealth} />
          <HealthGauge label="Network Usage" value={netUsage} icon={<Network size={14} />} color="blue" health={netHealth} />
        </div>
      </div>

      {/* Risk & Policy */}
      {/* NOTE: Risk Score has no scoring logic behind it anywhere in the backend yet
          (Layer 4/5 detection+correlation isn't built) - it will always read 0 until
          that exists. Showing it here as a real-looking number would be misleading,
          so it's held back until there's an actual score to show. */}
      <div className="grid grid-cols-1 gap-4">
        <div className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl p-5 shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
          <div className="text-[10px] font-bold tracking-widest text-slate-400 uppercase mb-2">Security Policy</div>
          <div className="text-sm font-semibold text-slate-800 mt-1">{agent.policy || "Default Policy"}</div>
        </div>
      </div>

      {/* Agent Logs */}
      <AgentLogs agentId={agent.id} />

      {/* Edit Modal */}
      <AnimatePresence>
        {showEditModal && (
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="bg-white rounded-3xl w-full max-w-xl p-8 shadow-2xl"
            >
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold">Edit Agent Details</h2>
                <button onClick={() => setShowEditModal(false)} className="text-slate-400 hover:text-slate-600"><X size={24} /></button>
              </div>

              <form onSubmit={onUpdateSubmit} className="space-y-5">
                <div className="grid grid-cols-2 gap-5">
                    <div>
                        <label className="block mb-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">Agent Group</label>
                        <select value={editData.agent_group} onChange={(e)=>setEditData({...editData, agent_group:e.target.value})} className="w-full border border-slate-200 rounded-xl p-3 text-sm">
                            <option>Default</option>
                            <option>Workstations</option>
                            <option>Servers</option>
                            <option>Critical Assets</option>
                        </select>
                    </div>
                    <div>
                        <label className="block mb-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">Environment</label>
                        <select value={editData.environment} onChange={(e)=>setEditData({...editData, environment:e.target.value})} className="w-full border border-slate-200 rounded-xl p-3 text-sm">
                            <option>Production</option>
                            <option>Staging</option>
                            <option>Development</option>
                            <option>Testing</option>
                        </select>
                    </div>
                    <div>
                        <label className="block mb-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">Department</label>
                        <input type="text" value={editData.department} onChange={(e)=>setEditData({...editData, department:e.target.value})} className="w-full border border-slate-200 rounded-xl p-3 text-sm" placeholder="IT, Finance, etc." />
                    </div>
                    <div>
                        <label className="block mb-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">Owner</label>
                        <input type="text" value={editData.owner} onChange={(e)=>setEditData({...editData, owner:e.target.value})} className="w-full border border-slate-200 rounded-xl p-3 text-sm" placeholder="Admin Name" />
                    </div>
                </div>

                <div>
                    <label className="block mb-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">Description</label>
                    <textarea rows="2" value={editData.description} onChange={(e)=>setEditData({...editData, description:e.target.value})} className="w-full border border-slate-200 rounded-xl p-3 text-sm resize-none" placeholder="Brief purpose of this agent..."></textarea>
                </div>

                <div>
                    <label className="block mb-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">Tags</label>
                    <input type="text" value={editData.tags} onChange={(e)=>setEditData({...editData, tags:e.target.value})} className="w-full border border-slate-200 rounded-xl p-3 text-sm" placeholder="web-server, dmz, pci-dss" />
                </div>

                <div className="flex justify-end gap-3 mt-8">
                  <button type="button" onClick={()=>setShowEditModal(false)} className="px-6 py-3 rounded-xl bg-slate-100 text-slate-600 font-bold text-sm hover:bg-slate-200 transition-colors">Cancel</button>
                  <button type="submit" className="px-6 py-3 rounded-xl bg-indigo-600 text-white font-bold text-sm shadow-lg shadow-indigo-500/25 hover:bg-indigo-700 transition-colors">Save Changes</button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

function InfoCard({ icon, label, value, mono, color, small }) {
  return (
    <motion.div
      initial="initial"
      animate="animate"
      variants={pageVariants}
      className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-xl p-4 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all"
    >
      <div className="flex items-center gap-2 mb-2">
        {icon && <span className="text-slate-400">{icon}</span>}
        <span className="text-[10px] font-bold tracking-widest text-slate-400 uppercase">{label}</span>
      </div>
      <div className={`font-semibold truncate ${mono ? "font-mono" : ""} ${color || "text-slate-900"} ${small ? "text-[10px]" : "text-sm"}`}>
        {value}
      </div>
    </motion.div>
  );
}

function HealthGauge({ label, value, icon, color, health }) {
  const colorMap = {
    indigo: { track: "bg-indigo-50", fill: "bg-gradient-to-r from-indigo-400 to-indigo-600", ring: "ring-indigo-100" },
    violet: { track: "bg-violet-50", fill: "bg-gradient-to-r from-violet-400 to-violet-600", ring: "ring-violet-100" },
    amber: { track: "bg-amber-50", fill: "bg-gradient-to-r from-amber-400 to-amber-600", ring: "ring-amber-100" },
    blue: { track: "bg-blue-50", fill: "bg-gradient-to-r from-blue-400 to-blue-600", ring: "ring-blue-100" }
  };
  const c = colorMap[color] || colorMap.indigo;

  return (
    <div className="bg-slate-50/50 border border-slate-100 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`w-7 h-7 rounded-lg ${c.track} flex items-center justify-center ring-2 ${c.ring}`}>
            {icon}
          </div>
          <span className="text-xs font-bold text-slate-700">{label}</span>
        </div>
        <span className={`text-xs font-bold ${health.color}`}>{value}%</span>
      </div>
      <div className="h-2 bg-slate-200/60 rounded-full overflow-hidden mb-3">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className={`h-full rounded-full ${c.fill}`}
        />
      </div>
      <div className="flex items-center gap-1.5">
        <span className={`w-1.5 h-1.5 rounded-full ${health.label === "Healthy" ? "bg-emerald-500" : health.label === "Warning" ? "bg-amber-500" : "bg-rose-500"} ${health.label === "Healthy" ? "animate-pulse" : ""}`}></span>
        <span className={`text-[10px] font-semibold ${health.color}`}>{health.label}</span>
      </div>
    </div>
  );
}
