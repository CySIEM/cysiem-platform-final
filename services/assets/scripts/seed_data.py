"""Seeds a handful of sample assets/IOCs/vulnerabilities for local demos
and manager walkthroughs. Run with: python -m scripts.seed_data
"""
import asyncio

from app.database.base import Base
from app.database.session import async_session_factory, engine
from app.models.asset import Asset
from app.models.ioc import IOC
from app.models.vulnerability import Vulnerability


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        session.add_all(
            [
                Asset(
                    asset_type="host",
                    primary_identifier="HOST-FIN01",
                    hostname="HOST-FIN01",
                    ip_addresses=["10.0.1.15"],
                    mac_addresses=["00:1A:2B:3C:4D:5E"],
                    usernames=["jdoe"],
                    risk_score=62,
                    severity="high",
                ),
                Asset(
                    asset_type="host",
                    primary_identifier="HOST-HR02",
                    hostname="HOST-HR02",
                    ip_addresses=["10.0.2.22"],
                    risk_score=18,
                    severity="low",
                ),
                IOC(ioc_type="ip", value="185.220.101.5", source="misp", confidence=0.95, is_malicious=True),
                IOC(ioc_type="domain", value="malicious-c2.example", source="otx", confidence=0.9, is_malicious=True),
                Vulnerability(
                    cve_id="CVE-2021-44228",
                    severity="critical",
                    description="Apache Log4j2 remote code execution (Log4Shell)",
                    affected_component="log4j-core",
                ),
            ]
        )
        await session.commit()
    print("Seed data inserted.")


if __name__ == "__main__":
    asyncio.run(seed())
