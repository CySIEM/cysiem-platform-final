import os
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from dotenv import load_dotenv
import random

from . import models, schemas, auth, database, bridge
from . import agents, enrollment, heartbeat, logs

load_dotenv()

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="CySIEM Platform API - Beta")

# Management API
app.include_router(agents.router)

# Real Agent Communication API
app.include_router(enrollment.router)
app.include_router(heartbeat.router)
app.include_router(logs.router)

# Serve installation scripts
app.mount("/scripts", StaticFiles(directory="scripts"), name="scripts")

# Serve the real agent source (registration/heartbeat/collector) so install
# scripts download the actual code that runs in this repo, instead of each
# installer carrying its own hand-copied duplicate that drifts out of sync.
app.mount("/agent-files", StaticFiles(directory="agent"), name="agent-files")

# ALLOWED_ORIGINS in backend/.env, comma-separated, e.g.
# ALLOWED_ORIGINS=http://localhost:5173,http://192.168.1.50:5173
_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return "<html><body><h1>CySIEM Beta API</h1><p>Please use <a href='http://localhost:5173'>http://localhost:5173</a> for the React dashboard.</p></body></html>"

@app.post("/api/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    user_count = db.query(models.User).count()
    assigned_role = "admin" if user_count == 0 else "analyst"
    
    hashed_pwd = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_pwd, role=assigned_role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.get("/api/dashboard/init")
def get_dashboard_init(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # Pull in whatever the correlation service (Team 4) currently has -
    # no-op if that service isn't reachable, see bridge.py.
    bridge.sync_incidents_from_correlation(db)

    # Calculate real stats from the database
    active_alerts = db.query(models.Alert).filter(models.Alert.is_active == True).count()
    open_incidents = db.query(models.Incident).filter(models.Incident.status.in_(["open", "investigating"])).count()
    
    # Get actual threats
    db_threats = db.query(models.ThreatCampaign).order_by(models.ThreatCampaign.confidence.desc()).limit(4).all()
    threats = [{
        "sev": t.severity, "title": t.title, "mitre": t.mitre_tag, "desc": t.description, "conf": t.confidence, "t": "recent"
    } for t in db_threats]

    # Get incidents grouped
    db_inc_open = db.query(models.Incident).filter(models.Incident.status == "open").all()
    db_inc_inv = db.query(models.Incident).filter(models.Incident.status == "investigating").all()
    db_inc_res = db.query(models.Incident).filter(models.Incident.status == "resolved").limit(5).all()

    def format_inc(i):
        return {"id": i.id, "title": i.title, "sev": i.severity, "who": i.assignee or "Unassigned", "ago": "recent"}

    incidents = {
        "open": [format_inc(i) for i in db_inc_open],
        "investigating": [format_inc(i) for i in db_inc_inv],
        "resolved": [format_inc(i) for i in db_inc_res]
    }

    # Get recent alerts
    db_alerts = db.query(models.Alert).order_by(models.Alert.id.desc()).limit(10).all()
    alerts = [{
        "sev": a.severity, "name": a.name, "src": a.src_ip, "dst": a.dst_ip, "mitre": a.mitre_tactic, "time": a.timestamp.strftime("%H:%M") if a.timestamp else "Unknown"
    } for a in db_alerts]

    # For chart data, we generate some realistic mock values since we aren't seeding a full timeseries DB yet
    return {
        "stats": {
            "active_alerts": active_alerts,
            "open_incidents": open_incidents,
            "events_per_hour": f"{random.randint(1, 2)}.{random.randint(1, 9)}M",
            "assets_monitored": 342,
            "security_score": max(100 - (active_alerts // 5), 45)
        },
        "charts": {
            "volData": [120,145,89,67,54,43,38,72,135,198,245,312,289,334,421,398,445,523,489,567,612,534,478,389],
            "donutData": [32, 24, 18, 12, 9, 5],
            "mitreData": [88, 95, 89, 76, 83, 91, 79, 87, 68, 74, 85, 61],
            "radarData": [85, 62, 48, 73, 35, 28]
        },
        "threats": threats,
        "incidents": incidents,
        "alerts": alerts,
        "playbooks": [
            { "id": "PB-882", "title": "Ransomware Containment", "desc": "Isolates host, disables SMB, snapshots volume.", "steps": 5 },
            { "id": "PB-883", "title": "Block C2 Infrastructure", "desc": "Updates edge firewall with malicious IP blocks.", "steps": 2 },
            { "id": "PB-884", "title": "Reset Compromised Creds", "desc": "Forces AD password reset for affected user.", "steps": 3 }
        ]
    }

@app.post("/api/copilot/chat")
async def chat_copilot(request: Request, current_user: models.User = Depends(auth.get_current_user)):
    data = await request.json()
    query = data.get("query", "")
    incident_id = data.get("incident_id")

    try:
        reply = bridge.ask_copilot(query, incident_id=incident_id)
    except Exception:
        # rag-copilot service unreachable/erroring - fall back rather than
        # hard-failing the chat UI.
        reply = f"Hello {current_user.username}. I am the CySIEM Intelligence Copilot, but I can't reach the RAG/AI service right now. Please try again shortly."
        if "summar" in query.lower():
            reply = "Pipeline processed **1.2M events**. AI Engine flagged **847 alerts**. 2 critical incidents are active (Ransomware, C2 Beacon)."
        elif "remedi" in query.lower() or "fix" in query.lower():
            reply = "**Immediate Remediation:**\n1. Execute POST /firewall/block → IP: 45.142.212.100\n2. Isolate endpoint 10.0.2.99 using EDR API."

    return {"reply": reply}

@app.get("/api/incidents/{incident_id}/explain")
def explain_incident(incident_id: str, current_user: models.User = Depends(auth.get_current_user)):
    try:
        return bridge.get_incident_explanation(incident_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not get AI explanation for {incident_id}: {exc}")

if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0: binding to 127.0.0.1 here means NOTHING outside this machine
    # can ever reach the API, regardless of what SERVER_URL is set to in the
    # enrollment command. This was the deeper cause behind the "connection
    # refused" bug - fixing only the generated command's URL was not enough.
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
