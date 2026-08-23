import React, { useState, useEffect } from 'react';
import AgentPage from "./components/AgentPage";
import AgentDetails from "./components/AgentDetails";
// import axios from 'axios';
import {
    loginUser, registerUser, getCurrentUser, getDashboard, getAgents,
    getAgentDetails, addAgent, updateAgent, deleteAgent, askCopilot, getRecentLogs,
    getIncidentExplanation } from "./api";
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, ShieldAlert, GitCommit, FileText, Bot, BookOpen, Clock, MonitorSmartphone, 
  TerminalSquare, Fingerprint, Lock, Shield, Server, Box, AlertTriangle, LogOut, CheckCircle2, X
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';

const COLORS = ['#6366f1', '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444']; 

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authMode, setAuthMode] = useState('login'); 
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState('');
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [userProfile, setUserProfile] = useState(null);

  const [activeTab, setActiveTab] = useState('overview');
  const [data, setData] = useState(null);
  const [chatInput, setChatInput] = useState("");
  const [chatLog, setChatLog] = useState([
    { role: 'bot', text: 'System operational. Connected to FastAPI Backend. I have full context on the current threat landscape. How can I assist?' }
  ]);
  const [time, setTime] = useState("");
  const [liveLogs, setLiveLogs] = useState([]);

  const [agents, setAgents] = useState([]);
  const [agentDetails, setAgentDetails] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showAddAgent, setShowAddAgent] = useState(false);
  const [agentsLastSync, setAgentsLastSync] = useState(null);
  const [agentsConnectionOk, setAgentsConnectionOk] = useState(true);

  // New agents state
  const [newAgent, setNewAgent] = useState({
    agent_group: "Default",
    operating_system: "Windows",
    environment: "Production"
  });

  const [enrollmentResult, setEnrollmentResult] = useState(null);
  
  // Interactive States
  const [toasts, setToasts] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [playbookLoading, setPlaybookLoading] = useState({});
  const [incidentExplanation, setIncidentExplanation] = useState(null);
  const [explanationLoading, setExplanationLoading] = useState(false);
  const [explanationError, setExplanationError] = useState(null);

  const addToast = (msg, type = 'info') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, msg, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
  };

  useEffect(() => {
    const token = localStorage.getItem("cysiem_token");
    if (token) {
      verifyUser();
    }
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC');
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    // This used to fabricate a random log line every second (fake hostnames,
    // fake "Cobalt Strike Beacon" detections that no detection engine ever
    // produced). It now polls the real cross-agent log feed instead - if no
    // agent has sent logs yet, this list is empty, and the UI says so
    // honestly instead of inventing activity.
    if (activeTab === 'logs' && isAuthenticated) {
      const poll = async () => {
        try {
          const res = await getRecentLogs(50);
          const real = res.data.map(log => ({
            l: log.level,
            s: log.host || `Agent ${log.agent_id}`,
            m: log.message,
            t: log.time,
          }));
          setLiveLogs(real.reverse()); // oldest first, matches flex-col-reverse rendering
        } catch (err) {
          // Leave whatever was last successfully loaded rather than clearing the view on a blip.
        }
      };
      poll();
      const interval = setInterval(poll, 5000);
      return () => clearInterval(interval);
    }
  }, [activeTab, isAuthenticated]);

  useEffect(() => {
    if (!selectedIncident) {
      setIncidentExplanation(null);
      setExplanationError(null);
      return;
    }
    setIncidentExplanation(null);
    setExplanationError(null);
    setExplanationLoading(true);
    getIncidentExplanation(selectedIncident.id)
      .then(res => setIncidentExplanation(res.data))
      .catch(err => setExplanationError(
        err.response?.data?.detail || "AI Copilot analysis is unavailable for this incident right now."
      ))
      .finally(() => setExplanationLoading(false));
  }, [selectedIncident]);

  useEffect(() => {
    // Live Agent Management: status/last-seen/heartbeat/counts refresh on
    // their own every 5s while this tab is open. No page reload - only the
    // `agents` state updates, so the table re-renders in place.
    if (activeTab === 'agents' && isAuthenticated) {
      const poll = async () => {
        try {
          const res = await getAgents();
          setAgents(res.data);
          setAgentsLastSync(new Date());
          setAgentsConnectionOk(true);
        } catch (err) {
          setAgentsConnectionOk(false);
        }
      };
      poll();
      const interval = setInterval(poll, 5000);
      return () => clearInterval(interval);
    }
  }, [activeTab, isAuthenticated]);

  useEffect(() => {
    // Live Agent Details: CPU/RAM/disk/network/uptime/status and the
    // agent's own event stream refresh every 5s while its detail page is
    // open, so a demo doesn't need a manual refresh to show ACTIVE or new
    // events landing. Depends on the id only (not the whole object) so
    // this doesn't tear down and restart the interval on every poll tick.
    const agentId = selectedAgent?.id;
    if (agentId && isAuthenticated) {
      const poll = async () => {
        try {
          const detail = await getAgentDetails(agentId);
          setAgentDetails(detail.data);
          setAgentsLastSync(new Date());
          setAgentsConnectionOk(true);
        } catch (err) {
          setAgentsConnectionOk(false);
        }
      };
      const interval = setInterval(poll, 5000);
      return () => clearInterval(interval);
    }
  }, [selectedAgent?.id, isAuthenticated]);

  const verifyUser = async () => {
    try {
      const res = await getCurrentUser();
      setUserProfile(res.data);
      setIsAuthenticated(true);
      fetchData();
      fetchAgents();
      addToast(`Welcome back, ${res.data.username}`, "success");
    }catch (err) {
      localStorage.removeItem("cysiem_token");
      setIsAuthenticated(false);
    }
  };


  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError("");
    try {
      if (authMode === "register") {
        await registerUser({
          username,
          password,
        });
        addToast(
          "Account created successfully. Please login.",
          "success"
        );
        setAuthMode("login");
        setUsername("");
        setPassword("");
      }else {
        const formData = new URLSearchParams();
        formData.append("username", username);
        formData.append("password", password);
        const res = await loginUser(formData);
        localStorage.setItem(
          "cysiem_token",
          res.data.access_token
        );
        await verifyUser();
      }
    }catch (err) {
      let message = "Authentication failed.";
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          message = err.response.data.detail
            .map((e) => e.msg)
            .join("\n");
        }else {
          message = err.response.data.detail;
        }
      }
      setAuthError(message);
    }finally {
      setAuthLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("cysiem_token");
    setIsAuthenticated(false);
    setUserProfile(null);
    setData(null);
    setUsername("");
    setPassword("");
    setAgentDetails(null);
    setSelectedAgent(null);
  };

  const fetchData = async () => {
    try {
      const res = await getDashboard();
      setData(res.data);
    }catch (err) {
      addToast("Error syncing with backend", "error");
    }
  };

  // New agents fetch function
  const fetchAgents = async () => {
    try {
      const res = await getAgents();
      setAgents(res.data);
    }catch (err) {
      addToast("Unable to fetch agents", "error");
    }
  };


  const fetchAgentDetails = async (id) => {
    try {
      const detail = await getAgentDetails(id);
      setAgentDetails(detail.data);
      setSelectedAgent(detail.data);
    }catch (err) {
      addToast("Failed to load agent details", "error");
    }
  };

  const handleAddAgent = async () => {
    try {
      const res = await addAgent(newAgent);
      addToast("Agent enrolled successfully", "success");
      setEnrollmentResult(res.data);
      setNewAgent({
        agent_group: "Default",
        operating_system: "Windows",
        environment: "Production"
      });
      fetchAgents();
    } catch (err) {
      addToast("Failed to enroll agent", "error");
    }
  };

  const handleDeleteAgent = async (id) => {
    if (!window.confirm("Are you sure you want to delete this agent and all its logs?")) return;
    try {
      await deleteAgent(id);
      addToast("Agent deleted successfully", "success");
      setSelectedAgent(null);
      setAgentDetails(null);
      fetchAgents();
    } catch (err) {
      addToast("Failed to delete agent", "error");
    }
  };

  const handleUpdateAgent = async (id, data) => {
    try {
      await updateAgent(id, data);
      addToast("Agent updated successfully", "success");
      fetchAgentDetails(id);
    } catch (err) {
      addToast("Failed to update agent", "error");
    }
  };

  const sendCopilot = async (msg) => {
    if (!msg.trim()) return;
    const newLog = [
      ...chatLog,
      {
        role: "user",
        text: msg,
      },
    ];
    setChatLog(newLog);
    setChatInput("");
    try {
      const res = await askCopilot(msg);
      setChatLog([
        ...newLog,
        {
          role: "bot",
          text: res.data.reply,
        },
      ]);
    }catch {
      setChatLog([
        ...newLog,
        {
          role: "bot",
          text: "Error connecting to AI Fabric.",
        },
      ]);
      addToast(
        "AI Copilot connection failed",
        "error"
      );
    }
  };


  const executePlaybook = (id) => {
    setPlaybookLoading(prev => ({...prev, [id]: true}));
    addToast(`Initializing Playbook ${id}...`, 'info');
    setTimeout(() => {
      setPlaybookLoading(prev => ({...prev, [id]: false}));
      addToast(`Playbook ${id} executed successfully on endpoint.`, 'success');
    }, 2500);
  };

  // --- Auth Screen ---
  if (!isAuthenticated) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-slate-50 z-50">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-100/50 via-slate-50 to-slate-50"
        ></motion.div>
        
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
          className="w-full max-w-md bg-white/70 backdrop-blur-xl border border-slate-200/60 rounded-3xl p-10 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)] relative z-10"
        >
          <div className="text-center mb-10">
            <motion.div 
              initial={{ scale: 0.8, rotate: -10 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ duration: 0.5, delay: 0.3, type: "spring" }}
              className="w-16 h-16 mx-auto bg-gradient-to-br from-indigo-500 to-violet-500 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-500/30 mb-6"
            >
              <Fingerprint className="w-8 h-8 text-white" />
            </motion.div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">CySIEM</h1>
            <p className="text-[10px] font-bold tracking-[0.3em] text-slate-400 mt-2 uppercase">Platform Access</p>
          </div>
          <form onSubmit={handleAuth} className="space-y-5">
            <div>
              <label className="block text-xs font-bold tracking-widest text-slate-500 mb-2">USERNAME</label>
              <input type="text" required value={username} onChange={e => setUsername(e.target.value)} className="w-full bg-slate-50/50 border border-slate-200 rounded-xl px-4 py-3.5 text-sm font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 transition-all shadow-inner" />
            </div>
            <div>
              <label className="block text-xs font-bold tracking-widest text-slate-500 mb-2">PASSWORD</label>
              <input type="password" required value={password} onChange={e => setPassword(e.target.value)} className="w-full bg-slate-50/50 border border-slate-200 rounded-xl px-4 py-3.5 text-sm font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 transition-all shadow-inner" />
            </div>
            
            <AnimatePresence>
              {authError && (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="text-xs font-semibold p-3 rounded-xl bg-red-50 text-red-600 border border-red-100"
                >
                  {authError}
                </motion.div>
              )}
            </AnimatePresence>

            <motion.button 
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              type="submit" 
              disabled={authLoading} 
              className="w-full py-4 mt-4 bg-gradient-to-r from-indigo-600 to-violet-600 rounded-xl text-white font-bold text-sm tracking-widest shadow-xl shadow-indigo-500/20 hover:shadow-indigo-500/40 transition-all flex items-center justify-center gap-2"
            >
              {authLoading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div> : (authMode === 'login' ? 'AUTHENTICATE' : 'CREATE ACCOUNT')}
            </motion.button>
            <div className="text-center mt-4">
              <button type="button" onClick={() => { setAuthMode(authMode === 'login' ? 'register' : 'login'); setAuthError(''); }} className="text-xs font-semibold text-slate-500 hover:text-indigo-600 transition-colors">
                {authMode === 'login' ? 'Need an account? Register here' : 'Already have an account? Login here'}
              </button>
            </div>
          </form>
        </motion.div>
        {/* Render Toasts on Login Screen too */}
        <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3">
          <AnimatePresence>
            {toasts.map(t => <Toast key={t.id} msg={t.msg} type={t.type} />)}
          </AnimatePresence>
        </div>
      </div>
    );
  }

  const volChartData = data?.charts?.volData?.map((v, i) => ({ time: `${i}:00`, value: v })) || [];
  const donutChartData = data?.charts?.donutData?.map((v, i) => ({ name: ['Malware', 'Phishing', 'DDoS', 'Insider', 'Exploit', 'Misc'][i], value: v })) || [];
  const mitreChartData = data?.charts?.mitreData?.map((v, i) => ({ name: `T10${i}`, value: v })) || [];
  const radarChartData = data?.charts?.radarData?.map((v, i) => ({ subject: ['Endpoint', 'Network', 'Cloud', 'Identity', 'Email', 'Web'][i], A: v, fullMark: 100 })) || [];
  
  const initials = userProfile?.username ? userProfile.username.substring(0, 2).toUpperCase() : 'AD';

  const pageVariants = {
    initial: { opacity: 0, y: 15 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1], staggerChildren: 0.1 } }
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 overflow-hidden font-sans selection:bg-indigo-500/20">
      
      {/* Sidebar */}
      <aside className="w-64 bg-white/60 backdrop-blur-xl border-r border-slate-200/60 flex flex-col shadow-[4px_0_24px_rgba(0,0,0,0.02)] z-20">
        <div className="p-6 border-b border-slate-100 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Shield className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="font-bold text-slate-900 tracking-tight leading-tight">CySIEM</div>
            <div className="text-[9px] font-bold tracking-[0.2em] text-slate-400 uppercase">Beta Platform</div>
          </div>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          <NavItem active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} icon={<Activity size={18} />} label="Overview" />
          <NavItem active={activeTab === 'pipeline'} onClick={() => setActiveTab('pipeline')} icon={<Box size={18} />} label="Architecture" />
          <NavItem active={activeTab === 'threats'} onClick={() => setActiveTab('threats')} icon={<ShieldAlert size={18} />} label="Threat Intel" />
          <NavItem active={activeTab === 'incidents'} onClick={() => setActiveTab('incidents')} icon={<GitCommit size={18} />} label="Incidents" badge={data?.incidents?.open?.length || 0} badgeColor="bg-rose-100 text-rose-700" />
          <NavItem active={activeTab === 'logs'} onClick={() => setActiveTab('logs')} icon={<TerminalSquare size={18} />} label="Event Logs" />
          <NavItem active={activeTab === 'copilot'} onClick={() => setActiveTab('copilot')} icon={<Bot size={18} />} label="AI Copilot" badge="RAG" badgeColor="bg-indigo-100 text-indigo-700" />
          <NavItem active={activeTab === 'playbooks'} onClick={() => setActiveTab('playbooks')} icon={<BookOpen size={18} />} label="Playbooks" />
          <NavItem active={activeTab === 'agents'} onClick={() => setActiveTab('agents')} icon={<MonitorSmartphone size={18} />} label="Agents" badge={agents.length} badgeColor="bg-blue-100 text-blue-700" />
        </nav>
        <div className="p-5 bg-gradient-to-t from-slate-100/80 to-transparent border-t border-slate-200/60 flex items-center gap-2 text-[10px] font-bold tracking-wider text-slate-500 uppercase">
          <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)] animate-pulse"></div>
          Live Sync Active
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden relative bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-50/40 via-slate-50 to-slate-50">
        
        {/* Header */}
        <header className="h-16 bg-white/70 backdrop-blur-xl border-b border-slate-200/60 px-8 flex items-center justify-between sticky top-0 z-10 shadow-[0_4px_20px_-10px_rgba(0,0,0,0.02)]">
          <motion.div 
            key={activeTab}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-xs font-bold tracking-widest text-slate-400"
          >
            CYSIEM <span className="mx-2 text-slate-200">/</span> <span className="text-slate-800">{activeTab.toUpperCase()}</span>
          </motion.div>
          <div className="flex items-center gap-6">
            <div className="text-[11px] font-mono font-medium text-slate-500 flex items-center gap-2 bg-slate-100/50 px-3 py-1.5 rounded-full border border-slate-200/50">
              <Clock size={12} className="text-slate-400" /> {time}
            </div>
            <div className="flex items-center gap-3 pl-6 border-l border-slate-200/60 relative group cursor-pointer">
              <div className="w-9 h-9 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center font-bold text-xs text-indigo-600 shadow-sm">{initials}</div>
              <div className="text-xs">
                <div className="font-bold text-slate-900">{userProfile?.username || 'User'}</div>
                <div className="text-slate-500 font-medium">{userProfile?.role || 'Analyst'}</div>
              </div>
              {/* Dropdown menu */}
              <div className="absolute right-0 top-12 pt-2 hidden group-hover:block w-40">
                <motion.div 
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white/90 backdrop-blur-xl border border-slate-200 rounded-xl shadow-xl overflow-hidden py-1"
                >
                  <button onClick={logout} className="w-full text-left px-4 py-2.5 flex items-center gap-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 transition-colors">
                    <LogOut size={14} /> End Session
                  </button>
                </motion.div>
              </div>
            </div>
          </div>
        </header>

        {/* Scrollable Area */}
        <div className="flex-1 overflow-y-auto p-8">
          <AnimatePresence mode="wait">
            {!data ? (
              <motion.div 
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full flex flex-col items-center justify-center gap-4 text-slate-400 font-mono text-sm"
              >
                <div className="w-8 h-8 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin"></div>
                SYNCING WITH FABRIC...
              </motion.div>
            ) : (
              <motion.div 
                key={activeTab}
                variants={pageVariants}
                initial="initial"
                animate="animate"
                className="max-w-[1600px] mx-auto"
              >
                
                {/* OVERVIEW TAB */}
                {activeTab === 'overview' && (
                  <div className="space-y-6">
                    {/* KPI Bar */}
                    <div className="grid grid-cols-5 gap-4">
                      <StatCard val={data.stats.active_alerts} label="Active Alerts" trend="+12%" color="indigo" />
                      <StatCard val={data.stats.open_incidents} label="Open Incidents" trend="-3%" color="violet" />
                      <StatCard val={data.stats.events_per_hour} label="Events / Hour" trend="+4%" color="blue" />
                      <StatCard val={data.stats.assets_monitored} label="Assets Monitored" trend="0%" color="emerald" />
                      <StatCard val={data.stats.security_score} label="Security Score" trend="+1.2" color="slate" />
                    </div>

                    <div className="grid grid-cols-3 gap-6">
                      {/* Line Chart */}
                      <motion.div variants={pageVariants} className="col-span-2 bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.02)] relative overflow-hidden">
                        <div className="mb-6 relative z-10">
                          <h3 className="font-bold text-slate-900 text-lg tracking-tight">Global Threat Volume</h3>
                          <p className="text-xs text-slate-500 mt-0.5">Ingestion & Detection Rate (24H)</p>
                        </div>
                        <div className="h-72 relative z-10">
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={volChartData}>
                              <defs>
                                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                              <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} dy={10} />
                              <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} dx={-10} />
                              <RechartsTooltip 
                                contentStyle={{ backgroundColor: 'rgba(255,255,255,0.95)', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)', backdropFilter: 'blur(8px)' }} 
                                itemStyle={{ color: '#0f172a', fontWeight: 'bold' }}
                              />
                              <Line type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#6366f1', stroke: '#fff', strokeWidth: 3 }} fillOpacity={1} fill="url(#colorValue)" />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      </motion.div>

                      {/* Radar Chart */}
                      <motion.div variants={pageVariants} className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
                        <div className="mb-2">
                          <h3 className="font-bold text-slate-900 tracking-tight">MITRE Coverage</h3>
                          <p className="text-xs text-slate-500 mt-0.5">Detection Fabric Radar</p>
                        </div>
                        <div className="h-72">
                          <ResponsiveContainer width="100%" height="100%">
                            <RadarChart cx="50%" cy="50%" outerRadius="65%" data={radarChartData}>
                              <PolarGrid stroke="#f1f5f9" />
                              <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 10, fontWeight: 600 }} />
                              <Radar name="Coverage" dataKey="A" stroke="#8b5cf6" strokeWidth={2} fill="#8b5cf6" fillOpacity={0.2} />
                              <RechartsTooltip contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)' }} />
                            </RadarChart>
                          </ResponsiveContainer>
                        </div>
                      </motion.div>

                      {/* Pie Chart */}
                      <motion.div variants={pageVariants} className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
                        <div className="mb-2">
                          <h3 className="font-bold text-slate-900 tracking-tight">Threat Breakdown</h3>
                          <p className="text-xs text-slate-500 mt-0.5">Classified by AI Engine</p>
                        </div>
                        <div className="h-72">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie data={donutChartData} innerRadius={65} outerRadius={90} paddingAngle={4} dataKey="value" stroke="none">
                                {donutChartData.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                              </Pie>
                              <RechartsTooltip contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)' }} />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                      </motion.div>

                      {/* Alert Table */}
                      <motion.div variants={pageVariants} className="col-span-2 bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
                        <div className="mb-6 flex justify-between items-end">
                          <div>
                            <h3 className="font-bold text-slate-900 text-lg tracking-tight">Database Alert Stream</h3>
                            <p className="text-xs text-slate-500 mt-0.5">Live SQLite queries from Detection Fabric</p>
                          </div>
                          <button onClick={() => addToast('Querying full historical alert database...', 'info')} className="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition-colors bg-indigo-50 px-3 py-1.5 rounded-lg">VIEW ALL</button>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-sm">
                            <thead>
                              <tr className="text-[10px] font-bold tracking-widest text-slate-400 uppercase border-b border-slate-100">
                                <th className="pb-3 font-medium">Severity</th>
                                <th className="pb-3 font-medium">Alert Definition</th>
                                <th className="pb-3 font-medium">Source</th>
                                <th className="pb-3 font-medium">Destination</th>
                                <th className="pb-3 font-medium">Tactic</th>
                                <th className="pb-3 font-medium text-right">Time</th>
                              </tr>
                            </thead>
                            <tbody>
                              {data.alerts.map((a, i) => (
                                <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/80 transition-colors group">
                                  <td className="py-4">
                                    <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider ${a.sev === 'critical' ? 'bg-rose-100 text-rose-700' : (a.sev === 'high' ? 'bg-orange-100 text-orange-700' : 'bg-yellow-100 text-yellow-700')}`}>
                                      {a.sev}
                                    </span>
                                  </td>
                                  <td className="py-4 font-semibold text-slate-800">{a.name}</td>
                                  <td className="py-4 font-mono text-xs text-slate-500">{a.src}</td>
                                  <td className="py-4 font-mono text-xs text-slate-500">{a.dst}</td>
                                  <td className="py-4 font-mono text-xs font-bold text-indigo-600">{a.mitre}</td>
                                  <td className="py-4 font-mono text-xs text-slate-400 text-right">{a.time}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </motion.div>
                    </div>
                  </div>
                )}

                {/* ARCHITECTURE TAB */}
                {activeTab === 'pipeline' && (
                  <div>
                    <div className="mb-8">
                      <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">System Architecture</h1>
                      <p className="text-slate-500">End-to-end data ingestion and analysis pipeline</p>
                    </div>
                    <div className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-3xl p-10 flex flex-col gap-0 max-w-4xl shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
                      <PipelineStage team="TEAM 1" name="Data Collection" desc="Ingests logs from EDR, Firewalls, and Cloud Providers." tags={['Logstash', 'Filebeat', 'Kafka']} color="bg-blue-500" />
                      <PipelineStage team="TEAM 2" name="Asset Intelligence" desc="Enriches logs with CMDB context and vulnerability data." tags={['Context Engine', 'Asset DB']} color="bg-cyan-500" />
                      <PipelineStage team="TEAM 3" name="Detection Fabric" desc="AI models flag anomalies and malicious signatures." tags={['Hugging Face', 'PyTorch']} color="bg-emerald-500" />
                      <PipelineStage team="TEAM 4" name="Correlation" desc="Groups isolated alerts into actionable incidents." tags={['Graph DB', 'Rule Engine']} color="bg-amber-500" />
                      <PipelineStage team="TEAM 5" name="Knowledge Base" desc="RAG pipeline providing automated recommendations." tags={['Ollama', 'ChromaDB', 'FAISS']} color="bg-rose-500" />
                      <PipelineStage team="TEAM 6" name="Dashboard & Beta Backend" desc="Provides visualization, SQLite database, and Playbooks." tags={['React', 'FastAPI', 'SQLite']} color="bg-indigo-500" isLast />
                    </div>
                  </div>
                )}

                {/* THREATS TAB */}
                {activeTab === 'threats' && (
                  <div>
                    <div className="mb-8">
                      <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">Threat Intelligence</h1>
                      <p className="text-slate-500">Active campaigns queried from SQLite Database</p>
                    </div>
                    <div className="grid grid-cols-2 gap-6">
                      {data.threats.map((t, i) => (
                        <motion.div 
                          key={i} 
                          variants={pageVariants}
                          whileHover={{ y: -4, boxShadow: '0 20px 40px -15px rgba(0,0,0,0.05)' }}
                          onClick={() => addToast(`Fetching complete STIX package for ${t.title}...`, 'info')}
                          className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl p-8 shadow-sm hover:border-indigo-300 transition-colors cursor-pointer group relative overflow-hidden"
                        >
                          <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-bl-[100px] -z-0 group-hover:bg-indigo-500/10 transition-colors"></div>
                          <div className="flex justify-between items-start mb-4 relative z-10">
                            <h3 className="font-bold text-xl text-slate-900 group-hover:text-indigo-600 transition-colors tracking-tight">{t.title}</h3>
                            <span className="px-3 py-1 rounded-lg text-[10px] font-bold uppercase tracking-widest bg-rose-100 text-rose-700">{t.sev}</span>
                          </div>
                          <div className="inline-block px-2.5 py-1 bg-slate-100 border border-slate-200/60 rounded-md text-xs font-mono font-bold text-slate-600 mb-5 relative z-10">{t.mitre}</div>
                          <p className="text-sm text-slate-600 mb-8 leading-relaxed relative z-10">{t.desc}</p>
                          <div className="flex justify-between items-center text-xs font-semibold text-slate-500 pt-5 border-t border-slate-100 relative z-10">
                            <span className="flex items-center gap-1.5 text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md">
                              <Activity size={14} /> Confidence: {t.conf}%
                            </span>
                            <span className="flex items-center gap-1.5 bg-slate-50 px-2 py-1 rounded-md">
                              <Clock size={14} /> {t.t}
                            </span>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {/* INCIDENTS TAB */}
                {activeTab === 'incidents' && (
                  <div>
                    <div className="mb-8">
                      <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">Incident Correlation</h1>
                      <p className="text-slate-500">Automatically grouped alerts managed by the Correlation Fabric.</p>
                    </div>
                    <div className="grid grid-cols-3 gap-6">
                      {['open', 'investigating', 'resolved'].map((col) => (
                        <div key={col} className="flex flex-col gap-4 bg-slate-200/30 p-5 rounded-3xl border border-slate-200/50 backdrop-blur-sm">
                          <div className="text-[11px] font-bold tracking-widest text-slate-500 uppercase pb-4 border-b-2 border-slate-200/50 flex justify-between items-center">
                            <span className="flex items-center gap-2">
                              <div className={`w-2.5 h-2.5 rounded-full ${col==='open'?'bg-rose-500':col==='investigating'?'bg-amber-500':'bg-emerald-500'} shadow-sm`}></div>
                              {col}
                            </span>
                            <span className="bg-white px-2.5 py-0.5 rounded-full shadow-sm border border-slate-200/60 text-slate-700">{data.incidents[col].length}</span>
                          </div>
                          {data.incidents[col].map((inc) => (
                            <motion.div 
                              key={inc.id}
                              variants={pageVariants}
                              whileHover={{ y: -3, scale: 1.01 }}
                              onClick={() => setSelectedIncident(inc)}
                              className="bg-white border border-slate-200/60 p-5 rounded-2xl shadow-sm hover:shadow-md hover:border-indigo-300 transition-all cursor-pointer group"
                            >
                              <div className="text-xs font-mono font-bold text-indigo-600 mb-2.5 bg-indigo-50 inline-block px-2 py-0.5 rounded-md">{inc.id}</div>
                              <div className="text-sm font-bold text-slate-800 mb-5 leading-snug group-hover:text-indigo-700 transition-colors">{inc.title}</div>
                              <div className="flex justify-between items-center text-[10px]">
                                <span className={`px-2.5 py-1 rounded-md font-bold uppercase tracking-wider ${inc.sev === 'critical' ? 'bg-rose-100 text-rose-700' : 'bg-orange-100 text-orange-700'}`}>{inc.sev}</span>
                                <span className="text-slate-500 flex items-center gap-1.5 font-medium"><div className="w-5 h-5 bg-slate-100 border border-slate-200 rounded-full flex items-center justify-center text-slate-600 text-[9px] font-bold">{inc.who?.[0]||'?'}</div>{inc.who}</span>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* LOGS TAB - Intentionally kept Dark for authentic terminal feel */}
                {activeTab === 'logs' && (
                  <div className="h-[calc(100vh-180px)] flex flex-col">
                    <div className="mb-6">
                      <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">Event Log Stream</h1>
                      <p className="text-slate-500">Live feed from enrolled agents, polled every 5s (Terminal theme)</p>
                    </div>
                    <motion.div variants={pageVariants} className="flex-1 bg-[#09090b] rounded-2xl overflow-hidden flex flex-col shadow-2xl ring-1 ring-slate-900/10">
                      <div className="bg-[#18181b] px-5 py-3.5 border-b border-white/5 flex items-center gap-4">
                        <div className="flex gap-2.5">
                          <div className="w-3.5 h-3.5 rounded-full bg-[#ff5f56] shadow-[0_0_10px_rgba(255,95,86,0.4)]"></div>
                          <div className="w-3.5 h-3.5 rounded-full bg-[#ffbd2e] shadow-[0_0_10px_rgba(255,189,46,0.4)]"></div>
                          <div className="w-3.5 h-3.5 rounded-full bg-[#27c93f] shadow-[0_0_10px_rgba(39,201,63,0.4)]"></div>
                        </div>
                        <div className="text-xs font-mono font-medium text-slate-400">cysiem@core-cluster:~$ tail -f /var/log/security.log</div>
                      </div>
                      <div className="flex-1 overflow-y-auto p-6 font-mono text-sm text-slate-300 leading-loose flex flex-col-reverse terminal-scroll">
                        <div>
                          {liveLogs.length === 0 && (
                            <div className="text-slate-500 italic py-4">
                              No agent has sent any log data yet. This feed is empty until a real endpoint with the CySIEM agent installed reports activity - it no longer fabricates events.
                            </div>
                          )}
                          {liveLogs.map((log, i) => (
                            <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="border-b border-slate-800/50 py-2 flex gap-4 hover:bg-slate-800/30 px-3 -mx-3 rounded transition-colors">
                              <span className="text-slate-500 shrink-0">{log.t || "—"}</span>
                              <span className={`w-20 shrink-0 font-bold ${log.l === 'CRITICAL' || log.l === 'HIGH' ? 'text-[#ff5f56]' : (log.l === 'MEDIUM' || log.l === 'WARNING' ? 'text-[#ffbd2e]' : 'text-[#44C4A1]')}`}>{log.l}</span>
                              <span className="w-32 shrink-0 text-[#64748b] truncate">[{log.s}]</span>
                              <span className="flex-1 text-slate-300">{log.m}</span>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  </div>
                )}

                {/* COPILOT TAB */}
                {activeTab === 'copilot' && (
                  <div className="h-[calc(100vh-180px)] max-w-5xl mx-auto">
                    <motion.div variants={pageVariants} className="flex h-full bg-white/80 backdrop-blur-xl border border-slate-200/80 rounded-3xl overflow-hidden shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)]">
                      <div className="w-80 bg-slate-50/50 border-r border-slate-200/60 p-8 flex flex-col relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-bl-full -z-0"></div>
                        <div className="flex items-center gap-4 mb-10 relative z-10">
                          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
                            <Bot size={24} />
                          </div>
                          <div>
                            <div className="font-bold text-slate-900 text-base tracking-tight">Intelligence Copilot</div>
                            <div className="text-[10px] font-bold tracking-widest text-indigo-600 uppercase mt-0.5">Powered by RAG</div>
                          </div>
                        </div>
                        <div className="text-[10px] font-bold tracking-widest text-slate-400 mb-5 uppercase relative z-10">Suggested Queries</div>
                        <div className="space-y-3 flex-1 relative z-10">
                          <CopilotBtn onClick={() => sendCopilot("Summarize the last 24 hours of threat activity.")}>Summarize 24h Activity</CopilotBtn>
                          <CopilotBtn onClick={() => sendCopilot("What are the top MITRE ATT&CK techniques observed?")}>Top MITRE Techniques</CopilotBtn>
                          <CopilotBtn onClick={() => sendCopilot("Provide remediation steps for active C2 beacon.")}>Remediation for C2</CopilotBtn>
                        </div>
                      </div>
                      <div className="flex-1 flex flex-col bg-white">
                        <div className="flex-1 p-8 overflow-y-auto space-y-8">
                          {chatLog.map((c, i) => (
                            <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={`flex gap-4 max-w-[85%] ${c.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}>
                              <div className={`w-10 h-10 rounded-2xl shrink-0 flex items-center justify-center text-sm font-bold shadow-md ${c.role === 'user' ? 'bg-indigo-50 border border-indigo-100 text-indigo-600' : 'bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-indigo-500/20'}`}>
                                {c.role === 'user' ? initials : <Bot size={18} />}
                              </div>
                              <div className={`p-5 rounded-3xl text-sm leading-relaxed whitespace-pre-wrap shadow-sm ${c.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-sm' : 'bg-slate-50 border border-slate-200/60 text-slate-800 rounded-tl-sm'}`}>
                                {c.text}
                              </div>
                            </motion.div>
                          ))}
                        </div>
                        <div className="p-6 border-t border-slate-200/60 bg-white">
                          <div className="flex gap-2 p-1.5 bg-slate-50 border border-slate-200 rounded-2xl focus-within:ring-4 focus-within:ring-indigo-500/20 focus-within:border-indigo-500 transition-all shadow-inner">
                            <input 
                              type="text" 
                              value={chatInput}
                              onChange={(e) => setChatInput(e.target.value)}
                              onKeyPress={(e) => e.key === 'Enter' && sendCopilot(chatInput)}
                              placeholder="Query threat intel, incidents, or ask for remediation..." 
                              className="flex-1 bg-transparent px-5 py-3 text-sm text-slate-900 focus:outline-none placeholder-slate-400 font-medium" 
                            />
                            <button onClick={() => sendCopilot(chatInput)} className="w-12 h-12 flex items-center justify-center text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 shadow-lg shadow-indigo-500/20 transition-all active:scale-95">
                              <Bot size={20} />
                            </button>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  </div>
                )}

                {/* PLAYBOOKS TAB */}
                {activeTab === 'playbooks' && (
                  <div>
                    <div className="mb-8">
                      <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">Response Playbooks</h1>
                      <p className="text-slate-500">Automated response workflows generated by AI</p>
                    </div>
                    <div className="grid grid-cols-3 gap-6">
                      {data.playbooks.map((pb, i) => (
                        <motion.div key={i} variants={pageVariants} className="bg-white/80 backdrop-blur-sm border border-slate-200/60 p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.02)] flex flex-col h-full relative overflow-hidden group">
                          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-indigo-500/5 to-violet-500/5 rounded-bl-[100px] -z-0 group-hover:scale-110 transition-transform duration-500"></div>
                          <div className="flex gap-5 items-center mb-6 relative z-10">
                            <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100 shadow-sm"><BookOpen size={24} /></div>
                            <div>
                              <div className="text-[10px] font-mono font-bold text-indigo-600 mb-1.5 bg-indigo-50 inline-block px-2 py-0.5 rounded">{pb.id}</div>
                              <div className="font-bold text-slate-900 text-lg leading-tight tracking-tight">{pb.title}</div>
                            </div>
                          </div>
                          <p className="text-sm text-slate-600 mb-10 flex-1 relative z-10 leading-relaxed">{pb.desc}</p>
                          <motion.button 
                            whileHover={userProfile?.role === 'admin' ? { scale: 1.02 } : {}}
                            whileTap={userProfile?.role === 'admin' ? { scale: 0.98 } : {}}
                            onClick={() => executePlaybook(pb.id)}
                            disabled={playbookLoading[pb.id] || userProfile?.role !== 'admin'}
                            className={`w-full py-4 rounded-xl font-bold text-xs tracking-widest transition-all relative z-10 shadow-lg flex items-center justify-center gap-2 ${playbookLoading[pb.id] ? 'bg-slate-100 text-slate-400 border border-slate-200' : (userProfile?.role !== 'admin' ? 'bg-slate-200 text-slate-400 cursor-not-allowed border border-slate-200' : 'bg-slate-900 text-white hover:bg-indigo-600 hover:shadow-indigo-500/25')}`}
                          >
                            {playbookLoading[pb.id] ? (
                               <><div className="w-4 h-4 border-2 border-slate-400/30 border-t-slate-400 rounded-full animate-spin"></div> EXECUTING...</>
                            ) : (userProfile?.role !== 'admin' ? <><Lock size={14} /> ADMIN ONLY</> : 'EXECUTE PLAYBOOK')}
                          </motion.button>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {/* AGENTS TAB */}
                {activeTab === "agents" && (
                  selectedAgent ? (
                      <AgentDetails
                          agentDetails={agentDetails}
                          setSelectedAgent={setSelectedAgent}
                          setAgentDetails={setAgentDetails}
                          handleDeleteAgent={handleDeleteAgent}
                          handleUpdateAgent={handleUpdateAgent}
                          lastSync={agentsLastSync}
                          connectionOk={agentsConnectionOk}
                      />
                  ) : (
                      <AgentPage
                          agents={agents}
                          setSelectedAgent={setSelectedAgent}
                          fetchAgentDetails={fetchAgentDetails}
                          setShowAddAgent={setShowAddAgent}
                          lastSync={agentsLastSync}
                          connectionOk={agentsConnectionOk}
                      />
                  )
                )}
              

            {/* ADD AGENT MODAL */}
            {showAddAgent && (
              <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                <div className="bg-white rounded-3xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-8 shadow-2xl">
                  {!enrollmentResult ? (
                    <>
                      <div className="flex justify-between items-center mb-6">
                        <h2 className="text-2xl font-bold">Enroll New Agent</h2>
                        <button onClick={() => setShowAddAgent(false)} className="text-slate-400 hover:text-slate-600"><X size={24} /></button>
                      </div>

                      <div className="grid grid-cols-1 gap-6">
                        <div>
                          <label className="block mb-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">Agent Group *</label>
                          <select value={newAgent.agent_group} onChange={(e)=>setNewAgent({...newAgent, agent_group:e.target.value})} className="w-full border border-slate-200 rounded-xl p-3 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all">
                            <option>Default</option>
                            <option>Workstations</option>
                            <option>Servers</option>
                            <option>Critical Assets</option>
                          </select>
                        </div>

                        <div>
                          <label className="block mb-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">Operating System *</label>
                          <select value={newAgent.operating_system} onChange={(e)=>setNewAgent({...newAgent, operating_system:e.target.value})} className="w-full border border-slate-200 rounded-xl p-3 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all">
                            <option>Windows</option>
                            <option>Ubuntu</option>
                            <option>Debian</option>
                            <option>Kali Linux</option>
                            <option>CentOS</option>
                            <option>Fedora</option>
                            <option>Linux (Generic)</option>
                          </select>
                          <p className="mt-1 text-[10px] text-slate-400">
                            macOS isn't listed - real event/log collection isn't implemented for it yet, only Windows and Linux support the full pipeline end-to-end.
                          </p>
                        </div>

                        <div>
                          <label className="block mb-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">Environment (Optional)</label>
                          <select value={newAgent.environment} onChange={(e)=>setNewAgent({...newAgent, environment:e.target.value})} className="w-full border border-slate-200 rounded-xl p-3 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all">
                            <option>Production</option>
                            <option>Staging</option>
                            <option>Development</option>
                            <option>Testing</option>
                          </select>
                        </div>

                        <p className="text-[10px] text-slate-400 leading-relaxed">
                          Note: Hostname, IP address, and system details will be automatically detected once the agent connects to the platform.
                        </p>
                      </div>

                      <div className="flex justify-end gap-3 mt-8">
                        <button onClick={()=>setShowAddAgent(false)} className="px-6 py-3 rounded-xl bg-slate-100 text-slate-600 font-bold text-sm hover:bg-slate-200 transition-colors">Cancel</button>
                        <button onClick={handleAddAgent} className="px-6 py-3 rounded-xl bg-indigo-600 text-white font-bold text-sm shadow-lg shadow-indigo-500/25 hover:bg-indigo-700 transition-colors">Enroll Agent</button>
                      </div>
                    </>
                  ) : (
                    <div className="text-center">
                      <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6">
                        <CheckCircle2 size={32} />
                      </div>
                      <h2 className="text-2xl font-bold mb-2">Enrollment Successful</h2>
                      <p className="text-slate-500 mb-8">Agent ID <span className="font-bold text-slate-800">#{enrollmentResult.id}</span> has been registered for <span className="font-bold text-slate-800">{enrollmentResult.operating_system}</span>. Run the command below on the target machine to complete enrollment.</p>

                      <div className="bg-slate-900 rounded-2xl p-6 text-left relative group">
                        <div className="flex justify-between items-center mb-3">
                          <span className="text-[10px] font-bold tracking-widest text-slate-500 uppercase">Installation Command ({enrollmentResult.operating_system})</span>
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(enrollmentResult.enrollment_commands);
                              addToast("Command copied to clipboard", "success");
                            }}
                            className="text-xs font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1.5"
                          >
                            <GitCommit size={14} /> COPY COMMAND
                          </button>
                        </div>
                        <code className="text-indigo-300 font-mono text-sm break-all leading-relaxed">
                          {enrollmentResult.enrollment_commands}
                        </code>
                      </div>

                      <div className="mt-8 space-y-4 text-left">
                        <h4 className="text-sm font-bold text-slate-900">Next Steps:</h4>
                        <ul className="text-xs text-slate-600 space-y-2.5">
                          <li className="flex gap-3"><div className="w-5 h-5 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0 font-bold">1</div> <span>Log in to the target <span className="font-bold">{enrollmentResult.operating_system}</span> machine with administrative privileges.</span></li>
                          <li className="flex gap-3"><div className="w-5 h-5 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0 font-bold">2</div> <span>Open a terminal (PowerShell for Windows, Bash for Linux).</span></li>
                          <li className="flex gap-3"><div className="w-5 h-5 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0 font-bold">3</div> <span>Paste and run the copied command. The agent will download and start automatically.</span></li>
                          <li className="flex gap-3"><div className="w-5 h-5 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0 font-bold">4</div> <span>Once the agent connects, the status will change to <span className="text-emerald-600 font-bold">Active</span> in the dashboard.</span></li>
                        </ul>
                      </div>

                      <button
                        onClick={() => {
                          setShowAddAgent(false);
                          setEnrollmentResult(null);
                        }}
                        className="w-full mt-10 py-4 bg-slate-900 text-white font-bold text-sm tracking-widest rounded-xl hover:bg-slate-800 transition-colors"
                      >
                        CLOSE & VIEW AGENT LIST
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}


              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Global Toast Container */}
        <div className="fixed bottom-8 right-8 z-50 flex flex-col gap-3 pointer-events-none">
          <AnimatePresence>
            {toasts.map(t => <Toast key={t.id} msg={t.msg} type={t.type} />)}
          </AnimatePresence>
        </div>

        {/* Incident Detail Modal */}
        <AnimatePresence>
          {selectedIncident && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/20 backdrop-blur-sm p-4"
              onClick={() => setSelectedIncident(null)}
            >
              <motion.div 
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                onClick={(e) => e.stopPropagation()}
                className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-2xl overflow-hidden"
              >
                <div className="p-8 border-b border-slate-100 flex justify-between items-start bg-slate-50/50">
                  <div>
                    <div className="text-[10px] font-mono font-bold text-indigo-600 mb-2 bg-indigo-50 inline-block px-2 py-0.5 rounded">{selectedIncident.id}</div>
                    <h2 className="text-2xl font-bold text-slate-900 tracking-tight">{selectedIncident.title}</h2>
                  </div>
                  <button onClick={() => setSelectedIncident(null)} className="p-2 bg-white border border-slate-200 rounded-full text-slate-400 hover:text-slate-900 shadow-sm transition-colors">
                    <X size={20} />
                  </button>
                </div>
                <div className="p-8 space-y-6">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100">
                      <div className="text-[10px] font-bold tracking-widest text-slate-400 uppercase mb-1">Severity</div>
                      <div className={`inline-block px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider ${selectedIncident.sev === 'critical' ? 'bg-rose-100 text-rose-700' : 'bg-orange-100 text-orange-700'}`}>{selectedIncident.sev}</div>
                    </div>
                    <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100">
                      <div className="text-[10px] font-bold tracking-widest text-slate-400 uppercase mb-1">Assigned Analyst</div>
                      <div className="text-sm font-semibold text-slate-900 flex items-center gap-2"><div className="w-6 h-6 bg-white border border-slate-200 rounded-full flex items-center justify-center text-slate-600 text-[10px] font-bold shadow-sm">{selectedIncident.who?.[0]}</div>{selectedIncident.who}</div>
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] font-bold tracking-widest text-slate-400 uppercase mb-3">Incident Timeline</div>
                    <div className="space-y-4 border-l-2 border-slate-200 ml-2 pl-4">
                      {(incidentExplanation?.timeline || []).length === 0 ? (
                        <div className="text-xs text-slate-400 italic">
                          {explanationLoading ? "Loading timeline from correlation service..." : "No timeline events available."}
                        </div>
                      ) : (
                        incidentExplanation.timeline.map((ev, i) => (
                          <div className="relative" key={ev.id || i}>
                            <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-indigo-500 ring-4 ring-white"></div>
                            <div className="text-xs text-slate-500 mb-1">{ev.timestamp || "Unknown time"}</div>
                            <div className="text-sm font-semibold text-slate-800">{ev.title || "Untitled event"}</div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] font-bold tracking-widest text-slate-400 uppercase mb-3 flex items-center gap-2">
                      <Bot size={12} /> AI Analysis {incidentExplanation && <span className="text-indigo-500 normal-case font-medium">(RAG-grounded)</span>}
                    </div>
                    <div className="bg-indigo-50/50 border border-indigo-100 rounded-2xl p-4 space-y-3">
                      {explanationLoading && (
                        <div className="text-sm text-slate-500 flex items-center gap-2">
                          <div className="w-3.5 h-3.5 border-2 border-indigo-300 border-t-indigo-600 rounded-full animate-spin"></div>
                          Copilot is analyzing this incident...
                        </div>
                      )}
                      {explanationError && (
                        <div className="text-sm text-rose-600">{explanationError}</div>
                      )}
                      {incidentExplanation && (
                        <>
                          <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{incidentExplanation.summary}</div>
                          {incidentExplanation.recommended_actions?.length > 0 && (
                            <div>
                              <div className="text-[10px] font-bold tracking-widest text-slate-400 uppercase mb-1">Recommended Actions</div>
                              <ul className="list-disc list-inside text-sm text-slate-700 space-y-0.5">
                                {incidentExplanation.recommended_actions.map((a, i) => <li key={i}>{a}</li>)}
                              </ul>
                            </div>
                          )}
                          {incidentExplanation.references?.length > 0 && (
                            <div className="text-[10px] text-slate-400">
                              Sources: {incidentExplanation.references.join(", ")}
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                  <div className="pt-4 flex gap-3">
                    <button onClick={() => { addToast('Assigning incident to your queue...', 'success'); setSelectedIncident(null); }} className="flex-1 py-3 bg-indigo-600 text-white font-bold text-xs tracking-widest rounded-xl shadow-lg shadow-indigo-500/25 hover:bg-indigo-700 transition-colors">CLAIM INCIDENT</button>
                    <button onClick={() => { setActiveTab('playbooks'); setSelectedIncident(null); }} className="flex-1 py-3 bg-white border border-slate-200 text-slate-700 font-bold text-xs tracking-widest rounded-xl shadow-sm hover:border-indigo-300 hover:text-indigo-600 transition-colors">RUN PLAYBOOK</button>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

// Components
const Toast = ({ msg, type }) => {
  const isSuccess = type === 'success';
  const isError = type === 'error';
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
      className="bg-white/90 backdrop-blur-xl border border-slate-200/60 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.1)] rounded-2xl p-4 flex items-center gap-3 w-80 pointer-events-auto"
    >
      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm ${isSuccess ? 'bg-emerald-50 text-emerald-500' : (isError ? 'bg-rose-50 text-rose-500' : 'bg-indigo-50 text-indigo-500')}`}>
        {isSuccess ? <CheckCircle2 size={16} /> : (isError ? <AlertTriangle size={16} /> : <Activity size={16} />)}
      </div>
      <div className="text-sm font-medium text-slate-800 leading-tight">{msg}</div>
    </motion.div>
  );
};

const NavItem = ({ active, onClick, icon, label, badge, badgeColor }) => (
  <button onClick={onClick} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all relative ${active ? 'bg-indigo-50/80 text-indigo-700 shadow-[inset_0_2px_4px_rgba(0,0,0,0.02)]' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100/80'}`}>
    {active && <motion.div layoutId="activeNav" className="absolute left-0 w-1 h-6 bg-indigo-600 rounded-r-full" />}
    <span className={active ? "text-indigo-600" : "text-slate-400"}>{icon}</span> 
    <span>{label}</span>
    {badge && <span className={`ml-auto px-2.5 py-0.5 rounded-md text-[10px] font-bold shadow-sm ${badgeColor}`}>{badge}</span>}
  </button>
);

const StatCard = ({ val, label, trend, color }) => {
  const isPos = trend.startsWith('+');
  return (
    <motion.div whileHover={{ y: -4, boxShadow: '0 10px 25px -5px rgba(0,0,0,0.05)' }} className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl p-5 shadow-sm relative overflow-hidden group transition-all">
      <div className={`absolute -right-6 -top-6 w-24 h-24 bg-${color}-500/5 rounded-full group-hover:scale-150 group-hover:bg-${color}-500/10 transition-all duration-700 ease-out`}></div>
      <div className="flex justify-between items-start mb-3 relative z-10">
        <div className="text-[10px] font-bold tracking-widest text-slate-500 uppercase">{label}</div>
        <div className={`text-[10px] font-bold px-2 py-0.5 rounded-md shadow-sm ${isPos ? 'bg-emerald-50 text-emerald-600 border border-emerald-100' : 'bg-slate-50 text-slate-600 border border-slate-200'}`}>{trend}</div>
      </div>
      <div className="text-3xl font-bold font-mono tracking-tighter text-slate-900 relative z-10">{val}</div>
    </motion.div>
  );
};

const PipelineStage = ({ team, name, desc, tags, color, isLast }) => (
  <div className="flex gap-8 group">
    <div className="w-48 text-right pt-4">
      <div className={`text-[10px] font-bold tracking-widest mb-1 uppercase ${color.replace('bg-', 'text-')}`}>{team}</div>
      <div className="font-bold text-slate-900 text-lg">{name}</div>
    </div>
    <div className="flex flex-col items-center w-10">
      <div className={`w-8 h-8 border-4 rounded-full flex items-center justify-center z-10 mt-3.5 bg-white shadow-sm transition-transform group-hover:scale-110 duration-300 ${color.replace('bg-', 'border-')}`}>
        <div className={`w-2.5 h-2.5 rounded-full ${color}`}></div>
      </div>
      {!isLast && <div className="w-0.5 flex-1 bg-slate-200 -my-2 min-h-[80px] group-hover:bg-slate-300 transition-colors"></div>}
    </div>
    <div className="flex-1 pt-4 pb-10">
      <div className="bg-slate-50/50 border border-slate-200/60 rounded-2xl p-6 shadow-sm group-hover:shadow-md transition-shadow group-hover:bg-white">
        <p className="text-sm text-slate-600 mb-5 leading-relaxed">{desc}</p>
        <div className="flex gap-2 flex-wrap">
          {tags.map(t => <span key={t} className="px-3 py-1.5 bg-white border border-slate-200 text-slate-700 text-[10px] font-bold rounded-lg shadow-sm">{t}</span>)}
        </div>
      </div>
    </div>
  </div>
);

const CopilotBtn = ({ children, onClick }) => (
  <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={onClick} className="w-full text-left px-5 py-4 bg-white border border-slate-200/60 rounded-2xl text-xs font-bold text-slate-700 hover:border-indigo-300 hover:shadow-md hover:text-indigo-700 transition-all">
    {children}
  </motion.button>
);