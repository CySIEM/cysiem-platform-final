import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronRight, ShieldAlert, Info, AlertTriangle, Shield, XCircle, Terminal,
  Search, Clock, ChevronDown, Loader2, WifiOff, RotateCcw
} from "lucide-react";
import { getAgentEvents } from "../api";

const severityConfig = {
  INFO: { label: "INFO", textColor: "text-slate-500", bgDot: "bg-slate-400", icon: <Info size={13} className="text-slate-500" /> },
  NORMAL: { label: "NORMAL", textColor: "text-blue-600", bgDot: "bg-blue-500", icon: <Info size={13} className="text-blue-600" /> },
  MEDIUM: { label: "MEDIUM", textColor: "text-amber-600", bgDot: "bg-amber-500", icon: <AlertTriangle size={13} className="text-amber-600" /> },
  HIGH: { label: "HIGH", textColor: "text-orange-600", bgDot: "bg-orange-500", icon: <ShieldAlert size={13} className="text-orange-600" /> },
  CRITICAL: { label: "CRITICAL", textColor: "text-rose-600", bgDot: "bg-rose-500", icon: <XCircle size={13} className="text-rose-600" /> }
};

const SOURCE_OPTIONS = [
  "All", "Authentication Failure", "Authentication Success", "Privilege Change",
  "Session Opened", "Session Closed", "Process Monitor", "Log Collector", "System"
];

const TIME_RANGE_OPTIONS = [
  { key: "5m", label: "Last 5 minutes" },
  { key: "15m", label: "Last 15 minutes" },
  { key: "30m", label: "Last 30 minutes" },
  { key: "1h", label: "Last 1 hour" },
  { key: "3h", label: "Last 3 hours" },
  { key: "6h", label: "Last 6 hours" },
  { key: "12h", label: "Last 12 hours" },
  { key: "24h", label: "Last 24 hours" },
  { key: "today", label: "Today" },
  { key: "yesterday", label: "Yesterday" },
  { key: "week", label: "This week" },
  { key: "7d", label: "Last 7 days" },
  { key: "30d", label: "Last 30 days" },
  { key: "custom", label: "Custom range" },
];

const PAGE_SIZE = 10;

// All range math is done in UTC, matching how timestamps are stored and
// displayed elsewhere in this app - mixing local-time boundaries with
// UTC-stored data is exactly the kind of silent bug that makes "Today"
// return the wrong events depending on the viewer's timezone.
function computeRange(preset, customStart, customEnd) {
  const now = new Date();
  const startOfUTCDay = (d) => new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));

  switch (preset) {
    case "5m": return { start: new Date(now - 5 * 60000), end: null };
    case "15m": return { start: new Date(now - 15 * 60000), end: null };
    case "30m": return { start: new Date(now - 30 * 60000), end: null };
    case "1h": return { start: new Date(now - 60 * 60000), end: null };
    case "3h": return { start: new Date(now - 3 * 3600000), end: null };
    case "6h": return { start: new Date(now - 6 * 3600000), end: null };
    case "12h": return { start: new Date(now - 12 * 3600000), end: null };
    case "24h": return { start: new Date(now - 24 * 3600000), end: null };
    case "today": return { start: startOfUTCDay(now), end: null };
    case "yesterday": {
      const startToday = startOfUTCDay(now);
      return { start: new Date(startToday - 24 * 3600000), end: startToday };
    }
    case "week": {
      const day = now.getUTCDay(); // 0=Sun
      const diffToMonday = (day === 0 ? 6 : day - 1);
      const monday = new Date(startOfUTCDay(now) - diffToMonday * 86400000);
      return { start: monday, end: null };
    }
    case "7d": return { start: new Date(now - 7 * 86400000), end: null };
    case "30d": return { start: new Date(now - 30 * 86400000), end: null };
    case "custom": {
      const start = customStart ? new Date(customStart) : null;
      const end = customEnd ? new Date(customEnd) : null;
      return { start, end };
    }
    default: return { start: new Date(now - 15 * 60000), end: null };
  }
}

export default function AgentLogs({ agentId }) {
  const [expandedId, setExpandedId] = useState(null);

  const [searchInput, setSearchInput] = useState("");   // raw typing
  const [search, setSearch] = useState("");              // debounced, actually queried
  const [severity, setSeverity] = useState("ALL");
  const [source, setSource] = useState("All");
  const [timeRange, setTimeRange] = useState("15m");
  const [customStart, setCustomStart] = useState({ date: "", time: "" });
  const [customEnd, setCustomEnd] = useState({ date: "", time: "" });
  const [appliedCustom, setAppliedCustom] = useState({ start: "", end: "" });
  const [timeRangeOpen, setTimeRangeOpen] = useState(false);

  const [limit, setLimit] = useState(PAGE_SIZE);
  const [events, setEvents] = useState([]);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  const [loading, setLoading] = useState(true);       // full-view loading (filter/range change)
  const [loadingMore, setLoadingMore] = useState(false); // "See more" in flight
  const [connectionOk, setConnectionOk] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);

  // Debounce the search box - don't fire a request per keystroke.
  useEffect(() => {
    const t = setTimeout(() => setSearch(searchInput.trim()), 400);
    return () => clearTimeout(t);
  }, [searchInput]);

  // Any filter/range change resets to the first page of results.
  useEffect(() => {
    setLimit(PAGE_SIZE);
  }, [search, severity, source, timeRange, appliedCustom]);

  const buildParams = useCallback((currentLimit) => {
    const { start, end } = computeRange(timeRange, appliedCustom.start, appliedCustom.end);
    return {
      page: 1,
      limit: currentLimit,
      search: search || undefined,
      severity: severity !== "ALL" ? severity : undefined,
      source: source !== "All" ? source : undefined,
      start_time: start ? start.toISOString() : undefined,
      end_time: end ? end.toISOString() : undefined,
    };
  }, [search, severity, source, timeRange, appliedCustom]);

  const fetchEvents = useCallback(async (currentLimit, { silent } = {}) => {
    if (!agentId) return;
    if (!silent) setLoading(true);
    try {
      const params = buildParams(currentLimit);
      const res = await getAgentEvents(agentId, params);
      setEvents(res.data.items || []);
      setTotal(res.data.total ?? 0);
      setHasMore(!!res.data.has_more);
      setConnectionOk(true);
      setErrorMsg(null);
    } catch (err) {
      setConnectionOk(false);
      if (!silent) {
        setErrorMsg(
          err?.response?.status === 400 ? "Invalid search or time range - adjust and try again."
          : err?.response?.status === 401 ? "Session expired - please sign in again."
          : "Could not load events from the backend."
        );
      }
    } finally {
      if (!silent) setLoading(false);
      setLoadingMore(false);
    }
  }, [agentId, buildParams]);

  // (Re)fetch on any filter/range/limit change.
  useEffect(() => {
    fetchEvents(limit);
  }, [limit, fetchEvents]);

  // Live polling: re-run the SAME query (same filters/time-range/limit)
  // every 5s. A non-matching new event never gets inserted, because it's
  // simply not part of the filtered result the backend returns. Silent -
  // no loading spinner disruption on every tick, only on real filter changes.
  useEffect(() => {
    if (!agentId) return;
    const interval = setInterval(() => fetchEvents(limit, { silent: true }), 5000);
    return () => clearInterval(interval);
  }, [agentId, limit, fetchEvents]);

  const handleSeeMore = () => {
    setLoadingMore(true);
    setLimit(l => l + PAGE_SIZE);
  };

  const applyCustomRange = () => {
    if (!customStart.date || !customEnd.date) return;
    const start = `${customStart.date}T${customStart.time || "00:00"}:00Z`;
    const end = `${customEnd.date}T${customEnd.time || "23:59"}:59Z`;
    setAppliedCustom({ start, end });
  };

  const toggleExpand = (id) => setExpandedId(expandedId === id ? null : id);
  const activeRangeLabel = TIME_RANGE_OPTIONS.find(o => o.key === timeRange)?.label || "Last 15 minutes";
  const filtersActive = search || severity !== "ALL" || source !== "All";

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200/60 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/30">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center">
            <Terminal size={16} className="text-indigo-600" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-sm tracking-tight">Agent Event Stream</h3>
            <p className="text-[10px] text-slate-400 font-medium tracking-wider uppercase">
              {filtersActive ? `Showing ${events.length} of ${total.toLocaleString()} matching events` : `Showing ${events.length} of ${total.toLocaleString()} events`}
            </p>
          </div>
        </div>
        <div className={`flex items-center gap-1.5 text-[10px] font-bold ${connectionOk ? "text-emerald-600" : "text-rose-600"}`}>
          {connectionOk ? <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> : <WifiOff size={12} />}
          {connectionOk ? "LIVE" : "RECONNECTING"}
        </div>
      </div>

      {/* Query controls */}
      <div className="px-6 py-4 border-b border-slate-100 bg-white space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={15} />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search events, PID, user, IP, process, message, MITRE technique..."
            className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
          />
        </div>

        <div className="flex flex-wrap gap-2 items-start">
          {/* Time range dropdown */}
          <div className="relative">
            <button
              onClick={() => setTimeRangeOpen(o => !o)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-[11px] font-semibold text-slate-600 hover:border-indigo-300"
            >
              <Clock size={12} />
              {activeRangeLabel}
              <ChevronDown size={12} className={`transition-transform ${timeRangeOpen ? "rotate-180" : ""}`} />
            </button>
            {timeRangeOpen && (
              <div className="absolute z-20 mt-1 w-48 bg-white border border-slate-200 rounded-lg shadow-lg py-1 max-h-72 overflow-y-auto">
                {TIME_RANGE_OPTIONS.map(opt => (
                  <button
                    key={opt.key}
                    onClick={() => { setTimeRange(opt.key); setTimeRangeOpen(false); }}
                    className={`w-full text-left px-3 py-1.5 text-[11px] hover:bg-indigo-50 ${timeRange === opt.key ? "text-indigo-600 font-bold" : "text-slate-600"}`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-[11px] font-semibold text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          >
            <option value="ALL">All severities</option>
            {Object.keys(severityConfig).map(k => <option key={k} value={k}>{k}</option>)}
          </select>

          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-[11px] font-semibold text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          >
            {SOURCE_OPTIONS.map(s => <option key={s} value={s}>{s === "All" ? "All sources" : s}</option>)}
          </select>
        </div>

        {timeRange === "custom" && (
          <div className="flex flex-wrap items-end gap-3 pt-1">
            <div className="flex flex-col gap-1">
              <label className="text-[9px] font-bold tracking-widest text-slate-400 uppercase">From (UTC)</label>
              <div className="flex gap-1.5">
                <input type="date" value={customStart.date} onChange={e => setCustomStart(s => ({ ...s, date: e.target.value }))}
                  className="px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-[11px]" />
                <input type="time" value={customStart.time} onChange={e => setCustomStart(s => ({ ...s, time: e.target.value }))}
                  className="px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-[11px]" />
              </div>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[9px] font-bold tracking-widest text-slate-400 uppercase">To (UTC)</label>
              <div className="flex gap-1.5">
                <input type="date" value={customEnd.date} onChange={e => setCustomEnd(s => ({ ...s, date: e.target.value }))}
                  className="px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-[11px]" />
                <input type="time" value={customEnd.time} onChange={e => setCustomEnd(s => ({ ...s, time: e.target.value }))}
                  className="px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-[11px]" />
              </div>
            </div>
            <button
              onClick={applyCustomRange}
              disabled={!customStart.date || !customEnd.date}
              className="px-4 py-1.5 bg-indigo-600 text-white rounded-lg text-[11px] font-bold disabled:opacity-40 disabled:cursor-not-allowed hover:bg-indigo-700"
            >
              Apply
            </button>
          </div>
        )}
      </div>

      {/* Body */}
      {loading ? (
        <div className="py-16 flex flex-col items-center justify-center gap-2 text-slate-400">
          <Loader2 size={20} className="animate-spin" />
          <span className="text-xs font-medium">Loading events…</span>
        </div>
      ) : errorMsg ? (
        <div className="py-14 flex flex-col items-center justify-center gap-3 text-center px-6">
          <WifiOff size={22} className="text-rose-400" />
          <p className="text-sm text-slate-500">{errorMsg}</p>
          <button
            onClick={() => fetchEvents(limit)}
            className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-700"
          >
            <RotateCcw size={12} /> Retry
          </button>
        </div>
      ) : events.length === 0 ? (
        <div className="py-14 text-center text-slate-400 text-sm italic px-6">
          {search
            ? "No events match your search."
            : filtersActive
              ? "No events found for the selected filters."
              : "No events found for the selected time range."}
        </div>
      ) : (
        <>
          {/* Table Header */}
          <div className="bg-slate-50/80 border-b border-slate-200/60 px-6 py-2.5 flex items-center gap-0 text-[10px] font-bold tracking-widest text-slate-400 uppercase">
            <div className="w-6"></div>
            <div className="w-24 shrink-0">Timestamp</div>
            <div className="w-24 shrink-0">Severity</div>
            <div className="w-40 shrink-0">Source</div>
            <div className="w-20 shrink-0">PID</div>
            <div className="flex-1">Description</div>
          </div>

          {/* Log Rows */}
          <div className="max-h-[600px] overflow-y-auto">
            {events.map((log, index) => {
              const sev = severityConfig[log.level] || severityConfig.INFO;
              const rowKey = log.id ?? index;
              const isExpanded = expandedId === rowKey;

              return (
                <React.Fragment key={rowKey}>
                  <div
                    onClick={() => toggleExpand(rowKey)}
                    className={`px-6 py-2.5 flex items-center gap-0 cursor-pointer border-b border-slate-50 transition-all hover:bg-slate-50 group ${
                      isExpanded ? "bg-indigo-50/40 border-b-transparent sticky top-0 bottom-0 z-10" : ""
                    }`}
                  >
                    <div className="w-6 shrink-0">
                      <ChevronRight
                        size={13}
                        className={`text-slate-300 transition-transform duration-200 group-hover:text-indigo-500 ${isExpanded ? "rotate-90 text-indigo-600" : ""}`}
                      />
                    </div>
                    <div className="w-24 shrink-0 font-mono text-[11px] text-slate-500">
                      {log.time || (log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : "—")}
                    </div>
                    <div className="w-24 shrink-0">
                      <span className={`inline-flex items-center gap-1.5 text-[10px] font-bold tracking-wider uppercase ${sev.textColor}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${sev.bgDot}`}></span>
                        {sev.label}
                      </span>
                    </div>
                    <div className="w-40 shrink-0 text-[11px] text-slate-600 font-semibold truncate pr-4">
                      {log.source || "—"}
                    </div>
                    <div className="w-20 shrink-0 font-mono text-[11px] text-slate-400">
                      {log.pid ?? "N/A"}
                    </div>
                    <div className="flex-1 text-[11px] text-slate-700 truncate font-medium">
                      {log.message || "—"}
                    </div>
                  </div>

                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden bg-indigo-50/20"
                      >
                        <div className="px-6 py-5 border-b border-indigo-100/50 border-l-4 border-l-indigo-500 mx-6 my-2 rounded-r-xl bg-white shadow-inner">
                          <div className="grid grid-cols-3 gap-x-8 gap-y-4">
                            <DetailRow label="Timestamp" value={log.timestamp} mono />
                            <DetailRow label="Severity" value={log.level} />
                            <DetailRow label="Source" value={log.source} />

                            <DetailRow label="Event ID" value={log.event_id} mono />
                            <DetailRow label="Category" value={log.category} />
                            <DetailRow label="Host" value={log.host} />

                            <DetailRow label="User" value={log.user} />
                            <DetailRow label="Process" value={log.process} mono />
                            <DetailRow label="PID" value={log.pid} mono emptyLabel="N/A" />

                            <DetailRow label="IP Address" value={log.ip_address} mono />
                            <div className="col-span-2">
                              <DetailRow label="Command Line" value={log.command_line} mono />
                            </div>

                            <div className="col-span-2">
                              <DetailRow label="File Path" value={log.file_path} mono />
                            </div>
                            <DetailRow label="SHA256" value={log.sha256} mono small />

                            <DetailRow label="MITRE Technique" value={log.mitre_technique} mono color="text-indigo-600 font-bold" emptyLabel="Unmapped" />
                            <div className="col-span-2">
                              <DetailRow label="Full Message" value={log.message} />
                            </div>
                          </div>

                          <div className="mt-6 flex justify-end">
                            <button
                              onClick={(e) => { e.stopPropagation(); setExpandedId(null); }}
                              className="text-[10px] font-bold text-slate-400 hover:text-indigo-600 uppercase tracking-widest flex items-center gap-1"
                            >
                              Collapse Event <ChevronRight size={10} className="-rotate-90" />
                            </button>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </React.Fragment>
              );
            })}
          </div>

          {/* Pagination footer */}
          <div className="p-3 bg-slate-50/50 border-t border-slate-100 text-center">
            {hasMore ? (
              <button
                onClick={handleSeeMore}
                disabled={loadingMore}
                className="inline-flex items-center gap-1.5 text-[11px] font-bold text-indigo-600 hover:text-indigo-700 disabled:opacity-50"
              >
                {loadingMore ? <><Loader2 size={12} className="animate-spin" /> Loading more events…</> : "See more events"}
              </button>
            ) : (
              <span className="text-[10px] text-slate-400 font-medium italic">
                {total > PAGE_SIZE ? "No more events for the selected time range." : "Real-time event streaming active."}
              </span>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function DetailRow({ label, value, mono, small, color, emptyLabel = "—" }) {
  return (
    <div className="space-y-1">
      <div className="text-[9px] font-bold tracking-widest text-slate-400 uppercase">{label}</div>
      <div className={`${color || "text-slate-700"} ${mono ? "font-mono" : ""} ${small ? "text-[10px]" : "text-[11px]"} break-all leading-relaxed bg-slate-50/50 p-1.5 rounded border border-slate-100/50`}>
        {value ?? emptyLabel}
      </div>
    </div>
  );
}
