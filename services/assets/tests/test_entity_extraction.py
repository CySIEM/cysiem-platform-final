from app.core.entity_extractor import entity_extractor
from app.core.constants import EntityType


def test_extracts_ip_address():
    entities = entity_extractor.extract("firewall DENY SRC=192.168.1.10 DST=10.0.0.5")
    values = [e.value for e in entities if e.entity_type == EntityType.IP_ADDRESS]
    assert "192.168.1.10" in values
    assert "10.0.0.5" in values


def test_extracts_cve():
    entities = entity_extractor.extract("Host exploited via CVE-2021-44228 (log4shell)")
    cves = [e.value for e in entities if e.entity_type == EntityType.CVE]
    assert "CVE-2021-44228" in cves


def test_extracts_hostname_and_username():
    entities = entity_extractor.extract("user=jdoe logon on HOST-FIN01 succeeded")
    hostnames = [e.value for e in entities if e.entity_type == EntityType.HOSTNAME]
    usernames = [e.value for e in entities if e.entity_type == EntityType.USERNAME]
    assert "HOST-FIN01" in hostnames
    assert "jdoe" in usernames


def test_dedupes_repeated_entities():
    entities = entity_extractor.extract("192.168.1.10 talked to 192.168.1.10 again")
    ip_matches = [e for e in entities if e.entity_type == EntityType.IP_ADDRESS]
    assert len(ip_matches) == 1


def test_extracts_mac_both_separator_styles():
    # Colon-separated (Linux/most tooling) and dash-separated (Windows
    # ipconfig/eventlog) - both showed up in real asset inventory data.
    entities = entity_extractor.extract("MAC 00:0c:29:c1:57:a5, IP 192.168.30.30")
    macs = [e.value for e in entities if e.entity_type == EntityType.MAC_ADDRESS]
    assert "00:0c:29:c1:57:a5" in macs

    entities = entity_extractor.extract("MAC 00-0C-29-83-62-83, IP 192.168.20.30")
    macs = [e.value for e in entities if e.entity_type == EntityType.MAC_ADDRESS]
    assert "00-0C-29-83-62-83" in macs


def test_extract_narrative_skips_false_positive_usernames():
    # Regression test: prose like Windows event descriptions used to trip
    # the user=/account= keyword matcher and produce garbage usernames
    # ("Name", "Domain", "performs") - extract_narrative() must not do this.
    text = (
        "Account Name:\t\tWIN11-01$\n\tAccount Domain:\t\tWORKGROUP\n\n"
        "This event occurs when a user performs a read operation."
    )
    entities = entity_extractor.extract_narrative(text)
    usernames = [e.value for e in entities if e.entity_type == EntityType.USERNAME]
    assert usernames == []


def test_extract_narrative_still_finds_real_domains_and_emails():
    entities = entity_extractor.extract_narrative("EXECVE argv: ping google.com -c 200")
    domains = [e.value for e in entities if e.entity_type == EntityType.DOMAIN]
    assert "google.com" in domains
