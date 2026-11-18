import os
import glob
import yaml
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import SecurityEvent, DetectionRule, Alert


class RuleDetectionEngine:
    def __init__(self, rules_dir: str = "../detection-rules"):
        self.rules_dir = rules_dir
        self.cached_rules: List[Dict[str, Any]] = []
        self.load_rules_from_disk()

    def load_rules_from_disk(self):
        self.cached_rules = []
        rule_paths = [
            self.rules_dir,
            "detection-rules",
            "../detection-rules",
            "../../detection-rules"
        ]
        target_dir = None
        for path in rule_paths:
            if os.path.exists(path) and os.path.isdir(path):
                target_dir = path
                break

        if not target_dir:
            return

        for filepath in glob.glob(os.path.join(target_dir, "*.yaml")):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and isinstance(data, dict) and "id" in data:
                        self.cached_rules.append(data)
            except Exception as e:
                print(f"[RuleEngine] Error loading {filepath}: {e}")

    def sync_rules_to_db(self, db: Session):
        """
        Synchronizes file-based rules into the database detection_rules table
        """
        for r in self.cached_rules:
            existing = db.query(DetectionRule).filter(DetectionRule.rule_id == r["id"]).first()
            if not existing:
                new_rule = DetectionRule(
                    rule_id=r["id"],
                    name=r.get("name", r["id"]),
                    description=r.get("description", ""),
                    severity=r.get("severity", "MEDIUM").upper(),
                    category=r.get("category", "General"),
                    condition_yaml=yaml.dump(r.get("condition", {})),
                    is_enabled=r.get("is_enabled", True),
                    time_window_seconds=r.get("time_window_seconds", 60),
                    threshold=r.get("threshold", 5),
                    mitre_technique_id=r.get("mitre_technique_id"),
                    version=r.get("version", "1.0")
                )
                db.add(new_rule)
            else:
                existing.name = r.get("name", existing.name)
                existing.description = r.get("description", existing.description)
                existing.severity = r.get("severity", existing.severity).upper()
                existing.threshold = r.get("threshold", existing.threshold)
                existing.time_window_seconds = r.get("time_window_seconds", existing.time_window_seconds)
                existing.mitre_technique_id = r.get("mitre_technique_id", existing.mitre_technique_id)
        db.commit()

    def evaluate_event(self, event: SecurityEvent, db: Session) -> List[Dict[str, Any]]:
        """
        Evaluates a single incoming event against all active rules
        Returns list of generated alert dictionaries
        """
        generated_alerts = []
        rules = db.query(DetectionRule).filter(DetectionRule.is_enabled == True).all()

        for rule in rules:
            try:
                cond = yaml.safe_load(rule.condition_yaml) or {}
                matched, evidence = self._evaluate_condition(rule, cond, event, db)
                if matched:
                    # Prevent alert flooding: check if identical alert fired in last window
                    window_start = datetime.now(timezone.utc) - timedelta(seconds=rule.time_window_seconds)
                    recent_alert = db.query(Alert).filter(
                        Alert.rule_id == rule.id,
                        Alert.created_at >= window_start.replace(tzinfo=None)
                    ).first()

                    if not recent_alert:
                        alert_dict = {
                            "title": f"Rule Alert: {rule.name}",
                            "description": rule.description,
                            "severity": rule.severity,
                            "status": "OPEN",
                            "source": "RULE",
                            "rule_id": rule.id,
                            "event_id": event.id,
                            "mitre_technique": rule.mitre_technique_id,
                            "evidence": evidence
                        }
                        generated_alerts.append(alert_dict)
            except Exception as e:
                print(f"[RuleEngine] Error evaluating rule {rule.rule_id}: {e}")

        return generated_alerts

    def _evaluate_condition(
        self,
        rule: DetectionRule,
        cond: Dict[str, Any],
        event: SecurityEvent,
        db: Session
    ) -> (bool, Optional[Dict[str, Any]]):
        now = event.timestamp or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        window_start = now - timedelta(seconds=rule.time_window_seconds)
        window_start_naive = window_start.replace(tzinfo=None)

        # 1. Check Brute Force (RULE-001)
        if rule.rule_id == "RULE-001":
            if event.event_type == "auth_failure":
                query = db.query(SecurityEvent).filter(
                    SecurityEvent.event_type == "auth_failure",
                    SecurityEvent.timestamp >= window_start_naive
                )
                if event.source_ip:
                    query = query.filter(SecurityEvent.source_ip == event.source_ip)
                if event.username:
                    query = query.filter(SecurityEvent.username == event.username)
                
                count = query.count()
                if count >= rule.threshold:
                    return True, {
                        "trigger": "Threshold exceeded",
                        "failed_attempts": count,
                        "threshold": rule.threshold,
                        "source_ip": event.source_ip,
                        "username": event.username,
                        "time_window_seconds": rule.time_window_seconds
                    }

        # 2. Check Port Scan (RULE-002)
        elif rule.rule_id == "RULE-002":
            if event.event_source in ["zeek", "network"] and event.destination_port:
                query = db.query(SecurityEvent.destination_port).filter(
                    SecurityEvent.source_ip == event.source_ip,
                    SecurityEvent.timestamp >= window_start_naive,
                    SecurityEvent.destination_port.isnot(None)
                ).distinct()
                distinct_ports = [p[0] for p in query.all()]
                if len(distinct_ports) >= rule.threshold:
                    return True, {
                        "trigger": "Multiple distinct destination ports accessed",
                        "scanned_ports_count": len(distinct_ports),
                        "ports_sample": distinct_ports[:10],
                        "source_ip": event.source_ip,
                        "threshold": rule.threshold
                    }

        # 3. Check Suspicious DNS (RULE-003)
        elif rule.rule_id == "RULE-003":
            if "dns" in event.event_type.lower():
                raw = str(event.raw_data or "").lower()
                norm = str(event.normalized_data or "").lower()
                keywords = cond.get("suspicious_keywords", ["tunnel", "c2", "ngrok", "tor"])
                found = [k for k in keywords if k in raw or k in norm]
                if found:
                    return True, {
                        "trigger": "Suspicious DNS keyword detected",
                        "matched_keywords": found,
                        "source_ip": event.source_ip,
                        "dns_activity": str(event.normalized_data)
                    }

        # 4. Check Unusual Outbound Traffic (RULE-004)
        elif rule.rule_id == "RULE-004":
            norm = event.normalized_data or {}
            orig_bytes = norm.get("orig_bytes") or (event.raw_data or {}).get("bytes_sent") or 0
            min_bytes = cond.get("min_bytes_out", 5000000)
            if orig_bytes >= min_bytes:
                return True, {
                    "trigger": "Large outbound byte volume transferred",
                    "bytes_sent": orig_bytes,
                    "threshold_bytes": min_bytes,
                    "source_ip": event.source_ip,
                    "destination_ip": event.destination_ip
                }

        # 5. Check Excessive Connections (RULE-005)
        elif rule.rule_id == "RULE-005":
            if "conn" in event.event_type.lower() and event.destination_ip:
                count = db.query(SecurityEvent).filter(
                    SecurityEvent.destination_ip == event.destination_ip,
                    SecurityEvent.timestamp >= window_start_naive
                ).count()
                if count >= rule.threshold:
                    return True, {
                        "trigger": "Rapid connection surge targeting host",
                        "connection_count": count,
                        "destination_ip": event.destination_ip,
                        "threshold": rule.threshold
                    }

        # 6. Check Abnormal Auth (RULE-006)
        elif rule.rule_id == "RULE-006":
            if event.event_type == "auth_success" and event.username:
                # Prior failures in window?
                prior_fails = db.query(SecurityEvent).filter(
                    SecurityEvent.username == event.username,
                    SecurityEvent.event_type == "auth_failure",
                    SecurityEvent.timestamp >= window_start_naive
                ).count()
                if prior_fails >= 2:
                    return True, {
                        "trigger": "Successful login immediately following multiple failures",
                        "prior_failed_logins": prior_fails,
                        "username": event.username,
                        "source_ip": event.source_ip
                    }

        # 7. Check Repeated Suspicious Connections (RULE-007)
        elif rule.rule_id == "RULE-007":
            if event.destination_port and event.destination_port > 1024:
                count = db.query(SecurityEvent).filter(
                    SecurityEvent.source_ip == event.source_ip,
                    SecurityEvent.destination_ip == event.destination_ip,
                    SecurityEvent.destination_port == event.destination_port,
                    SecurityEvent.timestamp >= window_start_naive
                ).count()
                if count >= rule.threshold:
                    return True, {
                        "trigger": "Repeated high-port connections (potential C2 beacon)",
                        "attempts": count,
                        "source_ip": event.source_ip,
                        "destination_ip": event.destination_ip,
                        "destination_port": event.destination_port
                    }

        # 8. Check Unusual Process Spawn (RULE-008)
        elif rule.rule_id == "RULE-008":
            if event.event_type == "process_spawn":
                proc = str(event.process_name or "").lower()
                details = (event.normalized_data or {}).get("details", {})
                parent = str(details.get("parent_process") or "").lower()

                suspicious_binaries = cond.get("suspicious_binaries", ["nc", "bash", "powershell.exe", "cmd.exe", "whoami"])
                suspicious_parents = cond.get("parent_whitelist_violation", ["nginx", "apache2", "httpd", "python", "node"])

                matched_proc = any(b in proc for b in suspicious_binaries)
                matched_parent = any(p in parent for p in suspicious_parents)

                if matched_proc and matched_parent:
                    return True, {
                        "trigger": "Suspicious shell/binary spawned by web server or interpreter",
                        "spawned_process": event.process_name,
                        "parent_process": parent,
                        "process_pid": event.process_pid,
                        "host_id": event.host_id
                    }

        return False, None


rule_engine = RuleDetectionEngine()
