from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.models import ThreatIndicator


SAMPLE_INDICATORS = [
    {
        "indicator_type": "IP",
        "value": "198.51.100.45",
        "threat_type": "C2 Server",
        "severity": "CRITICAL",
        "confidence": 95,
        "source": "SentinelLab C2 Tracker",
    },
    {
        "indicator_type": "IP",
        "value": "203.0.113.88",
        "threat_type": "Active Scanner / Exploiter",
        "severity": "HIGH",
        "confidence": 90,
        "source": "Darknet Sensor Feed",
    },
    {
        "indicator_type": "IP",
        "value": "185.220.101.5",
        "threat_type": "Tor Exit Node",
        "severity": "MEDIUM",
        "confidence": 85,
        "source": "Tor Bulk Exit List",
    },
    {
        "indicator_type": "DOMAIN",
        "value": "evil-c2-beacon.xyz",
        "threat_type": "Malware C2 Domain",
        "severity": "CRITICAL",
        "confidence": 98,
        "source": "ThreatExchange Intelligence",
    },
    {
        "indicator_type": "DOMAIN",
        "value": "phishing-secure-portal.info",
        "threat_type": "Credential Harvester",
        "severity": "HIGH",
        "confidence": 88,
        "source": "Anti-Phishing Working Feed",
    }
]


def seed_sample_indicators(db: Session):
    for ind in SAMPLE_INDICATORS:
        existing = db.query(ThreatIndicator).filter(ThreatIndicator.value == ind["value"]).first()
        if not existing:
            new_ind = ThreatIndicator(
                indicator_type=ind["indicator_type"],
                value=ind["value"],
                threat_type=ind["threat_type"],
                severity=ind["severity"],
                confidence=ind["confidence"],
                source=ind["source"],
                is_active=True
            )
            db.add(new_ind)
    db.commit()


def check_threat_intelligence(
    db: Session,
    source_ip: Optional[str] = None,
    destination_ip: Optional[str] = None,
    domain: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Checks whether observed IP or domain matches known active threat indicators
    """
    targets = []
    if source_ip:
        targets.append(("IP", source_ip))
    if destination_ip:
        targets.append(("IP", destination_ip))
    if domain:
        targets.append(("DOMAIN", domain))

    now = datetime.now(timezone.utc)

    for ind_type, val in targets:
        match = db.query(ThreatIndicator).filter(
            ThreatIndicator.indicator_type == ind_type,
            ThreatIndicator.value == val,
            ThreatIndicator.is_active == True
        ).first()

        if match:
            # Check expiry if set
            if match.expires_at and match.expires_at.replace(tzinfo=timezone.utc) < now:
                continue

            # Compute threat intel score (0 - 100)
            base_score = match.confidence
            if match.severity == "CRITICAL":
                score = min(100.0, base_score * 1.0)
            elif match.severity == "HIGH":
                score = min(100.0, base_score * 0.85)
            elif match.severity == "MEDIUM":
                score = min(100.0, base_score * 0.6)
            else:
                score = min(100.0, base_score * 0.4)

            return {
                "matched": True,
                "indicator_id": match.id,
                "indicator_type": match.indicator_type,
                "value": match.value,
                "threat_type": match.threat_type,
                "severity": match.severity,
                "confidence": match.confidence,
                "source": match.source,
                "score": round(score, 2)
            }

    return None
