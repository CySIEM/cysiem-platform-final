# CySIEM - Frontend Dashboard (Team 6)

Welcome to the frontend repository for the CySIEM platform! This is a modern, premium web application built to serve as the "Single Pane of Glass" for our AI-powered Security Information and Event Management (SIEM) system.

## 🚀 Technologies Used
* **Framework:** React + Vite
* **Styling:** Tailwind CSS (v4)
* **Data Visualization:** Recharts
* **Icons:** Lucide React

## ✨ Features
* **Premium UI:** A highly polished Light Theme with glassmorphic elements and modern typography.
* **Live Dashboards:** Displays Active Alerts, Open Incidents, and System metrics.
* **Interactive Charts:** MITRE ATT&CK Radar Chart, Threat Volume Line Chart, and Pie Charts.
* **Event Log Stream:** A simulated terminal interface for raw log ingestion.
* **AI Copilot:** A chat interface integrated with Team 5's RAG Knowledge Base.
* **Incident Management:** Kanban-style boards for tracking correlated alerts.

## 🛠️ How to Run Locally

Because this is a full-stack application, you must run both the Frontend and the Backend.

### 1. Start the Backend (FastAPI + SQLite)
Open a terminal in the `backend` directory:
```bash
# Install requirements
pip install fastapi uvicorn sqlalchemy passlib bcrypt python-jose python-multipart

# Start the server
uvicorn api.main:app --reload
```
*The backend will run on `http://127.0.0.1:8000`*

### 2. Start the Frontend (React)
Open a new terminal in the `frontend` directory:
```bash
# Install dependencies
npm install

# Start the development server
npm run dev
```
*The frontend will run on `http://localhost:5173`*

## 🔒 Authentication
To log in, simply click **"Create Account"** on the main screen to register a local user in the SQLite database. Once registered, log in to access the dashboard.
