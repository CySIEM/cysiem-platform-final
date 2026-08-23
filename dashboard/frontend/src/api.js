import axios from "axios";

// Set VITE_API_BASE_URL in frontend/.env when the dashboard is not running
// on the same machine as the backend, e.g. VITE_API_BASE_URL=http://192.168.1.50:8000/api
const API = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api",
    headers: {
        "Content-Type": "application/json",
    },
});

API.interceptors.request.use((config) => {

    const token = localStorage.getItem("cysiem_token");

    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    return config;

});


// ----------------------
// Authentication
// ----------------------

export const loginUser = (data) =>
    API.post(
        "/auth/login",
        data,
        {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
        }
    );

export const registerUser = (data) =>
    API.post("/auth/register", data);

export const getCurrentUser = () =>
    API.get("/auth/me");


// ----------------------
// Dashboard
// ----------------------

export const getDashboard = () =>
    API.get("/dashboard/init");


// ----------------------
// Agents
// ----------------------

export const getAgents = () =>
    API.get("/agents");

export const getAgentDetails = (id) =>
    API.get(`/agents/${id}`);

export const getAgentLogs = (id) =>
    API.get(`/agents/${id}/logs`);

// Historical / filtered / paginated event query - powers the Agent Event
// Stream's search bar, time-range picker, and "See more events". Params
// are only included when set so the backend sees a clean, minimal query.
export const getAgentEvents = (agentId, params = {}) => {
    const clean = {};
    Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== "") clean[k] = v;
    });
    return API.get(`/agents/${agentId}/events`, { params: clean });
};

export const addAgent = (data) =>
    API.post("/enrollment/enroll", data);

export const updateAgent = (id, data) =>
    API.put(`/agents/${id}`, data);

export const deleteAgent = (id) =>
    API.delete(`/agents/${id}`);

export const reissueAgentToken = (id) =>
    API.post(`/enrollment/${id}/reissue-token`);


// ----------------------
// Logs (cross-agent feed for the Event Logs tab)
// ----------------------

export const getRecentLogs = (limit = 50) =>
    API.get("/logs/recent", { params: { limit } });


// ----------------------
// AI Copilot
// ----------------------

export const askCopilot = (query) =>
    API.post("/copilot/chat", {
        query,
    });


export default API;