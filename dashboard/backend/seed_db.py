import random
from datetime import datetime, timedelta
from api.database import SessionLocal, engine
from api import models

def seed_db():
    print("Creating tables...")
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if we already have data
    if db.query(models.Alert).first():
        print("Database already seeded. Skipping.")
        return
        
    print("Seeding alerts...")
    mitre_tags = ["T1110", "T1071", "T1486", "T1021", "T1558", "T1059"]
    for i in range(50):
        a = models.Alert(
            severity=random.choice(["critical", "high", "medium", "low"]),
            name=f"Suspicious Activity {i}",
            src_ip=f"10.0.{random.randint(1,5)}.{random.randint(1,254)}",
            dst_ip=f"192.168.1.{random.randint(1,100)}",
            mitre_tactic=random.choice(mitre_tags),
            confidence=random.randint(60, 99),
            is_active=random.choice([True, False])
        )
        db.add(a)

    print("Seeding incidents...")
    for i in range(15):
        inc = models.Incident(
            id=f"INC-2024-{100+i}",
            title=f"Correlation Event {i}",
            severity=random.choice(["critical", "high", "medium"]),
            status=random.choice(["open", "investigating", "resolved"]),
            assignee=random.choice(["SOC Analyst", "Threat Hunter", None])
        )
        db.add(inc)

    print("Seeding threats...")
    threats = [
        ("Ransomware Campaign", "critical", "T1486"),
        ("Cobalt Strike Beacon", "critical", "T1071"),
        ("Kerberoasting", "high", "T1558"),
        ("Data Exfiltration", "high", "T1048")
    ]
    for t in threats:
        th = models.ThreatCampaign(
            title=t[0],
            severity=t[1],
            mitre_tag=t[2],
            description="Automatically detected by AI Fabric",
            confidence=random.randint(85, 99)
        )
        db.add(th)

    db.commit()
    db.close()
    print("Database seeding complete!")

if __name__ == "__main__":
    seed_db()
