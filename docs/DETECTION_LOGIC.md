# SentinelAI Detection & Correlation Logic Specification

## 1. Overview

SentinelAI incorporates a dual-tier detection methodology:
1. **Rule-Based Detection Engine**: Deterministic, low-latency Sigma-inspired YAML rules for identifying known adversary tactics, techniques, and procedures (TTPs).
2. **Machine Learning Anomaly Engine**: Supervised classification (Random Forest) and unsupervised anomaly scoring (Isolation Forest) trained on standard network flow characteristics.
3. **Multi-Stage Event Correlation Engine**: Synthesizes cross-source telemetry across time windows to detect complex cyber attack sequences.
4. **Configurable Risk Scoring Engine**: Calculates an explainable 0–100 risk score based on multi-dimensional telemetry factors.

---

## 2. Rule-Based Detection Engine

All rules are authored in Sigma-inspired YAML syntax and placed under `backend/detection-rules/`. Each rule defines match criteria, time windows, occurrence thresholds, severity, and MITRE ATT&CK alignment.

### Anti-Flooding Alert Suppression
To prevent alert fatigue during sustained attacks (e.g., a SYN flood or multi-hour brute force), SentinelAI maintains a cooldown cache in memory. Once an alert triggers for an `(ip, rule_id)` pair, duplicate alerts are suppressed for `suppression_window_seconds` (default: 300 seconds), while updating the underlying event count.

### The 8 Core Detection Rules

#### Rule 1: Brute-Force Login Detection (`RULE-001`)
- **File**: `brute_force.yaml`
- **MITRE ATT&CK**: T1110 (Brute Force)
- **Severity**: HIGH
- **Condition**: Event type equals `AUTH_FAILED` or Suricata signature matching `SSH Brute Force`.
- **Threshold**: $\ge 5$ failed attempts from the same source IP.
- **Time Window**: 60 seconds.
- **Action**: Generates alert and tags event sequence for correlation.

#### Rule 2: Port Scanning Detection (`RULE-002`)
- **File**: `port_scan.yaml`
- **MITRE ATT&CK**: T1046 (Network Service Discovery)
- **Severity**: MEDIUM
- **Condition**: Network connections or Suricata signatures indicating port scan activity.
- **Threshold**: $\ge 15$ distinct destination ports contacted by the same source IP.
- **Time Window**: 30 seconds.
- **Action**: Generates alert with target port distribution.

#### Rule 3: Suspicious DNS Activity (`RULE-003`)
- **File**: `suspicious_dns.yaml`
- **MITRE ATT&CK**: T1071.004 (DNS Communication / Exfiltration)
- **Severity**: HIGH
- **Condition**: DNS query containing high Shannon entropy ($> 3.8$) or matching dynamic DNS domains (`.onion`, `.bit`, `*.duckdns.org`, `*.ngrok.io`).
- **Threshold**: 1 occurrence.
- **Time Window**: Instantaneous.
- **Action**: Alert flagged with suspected DGA / C2 channel.

#### Rule 4: Unusual Outbound Traffic (`RULE-004`)
- **File**: `unusual_traffic.yaml`
- **MITRE ATT&CK**: T1048 (Exfiltration Over Alternative Protocol)
- **Severity**: HIGH
- **Condition**: Outbound connection to external IP with transferred bytes exceeding 10 MB or connection duration $> 3600\text{s}$ over non-standard ports.
- **Threshold**: 1 occurrence.
- **Time Window**: Flow completion.

#### Rule 5: Excessive Network Connections (`RULE-005`)
- **File**: `excessive_connections.yaml`
- **MITRE ATT&CK**: T1499 (Endpoint Denial of Service)
- **Severity**: MEDIUM
- **Condition**: Source IP establishing connections at a rate exceeding 100 flows per minute.
- **Threshold**: $\ge 100$ connections.
- **Time Window**: 60 seconds.

#### Rule 6: Abnormal Authentication Behavior (`RULE-006`)
- **File**: `abnormal_auth.yaml`
- **MITRE ATT&CK**: T1078 (Valid Accounts)
- **Severity**: MEDIUM
- **Condition**: Authentication success outside normal operational hours (e.g. 01:00-05:00 local) or administrative login from a non-workstation subnet.
- **Threshold**: 1 occurrence.

#### Rule 7: Repeated Suspicious Connections (`RULE-007`)
- **File**: `repeated_suspicious_conn.yaml`
- **MITRE ATT&CK**: T1071 (Application Layer Protocol - C2 Beaconing)
- **Severity**: HIGH
- **Condition**: Periodic connection attempts to the same foreign IP at regular intervals (jitter $< 5\%$).
- **Threshold**: $\ge 8$ periodic connections.
- **Time Window**: 300 seconds.

#### Rule 8: Unusual Endpoint Process Activity (`RULE-008`)
- **File**: `unusual_process.yaml`
- **MITRE ATT&CK**: T1059 (Command and Scripting Interpreter)
- **Severity**: CRITICAL
- **Condition**: Execution of high-risk processes (`powershell.exe -enc`, `cmd.exe /c whoami`, `curl | bash`, `/bin/nc -e`, `mimikatz.exe`, `vssadmin delete shadows`).
- **Threshold**: 1 occurrence.
- **Time Window**: Instantaneous.

---

## 3. Multi-Stage Event Correlation Engine

Cyber adversaries rarely execute isolated, single-step operations. SentinelAI links events into coherent incident storylines using temporal sliding windows and relational graph attributes:

```
[10:00:00] Multiple Failed Logins (Brute Force)
     |
     v (Within 5 minutes, same Source IP / Host)
[10:01:15] Successful Authentication (Valid Account Compromise)
     |
     v (Within 10 minutes, same Host / User)
[10:02:40] Unusual Process Execution (cmd.exe / powershell.exe)
     |
     v (Within 15 minutes, same Host / Internal IP)
[10:03:50] Abnormal Outbound Connection (C2 Beaconing / Exfiltration)
```

### Correlation Criteria
1. **Entity Binding**: Matching `source_ip`, `host_id`, or `user_identity`.
2. **Temporal Window**: Default 15-minute sliding correlation window.
3. **Attack Chain Progression**: Events that span multiple MITRE ATT&CK tactics:
   - Initial Access $\to$ Execution $\to$ Lateral Movement $\to$ Exfiltration.
4. **Auto-Escalation**: When an attack chain spans $\ge 2$ stages, an Incident is automatically generated with severity escalated to `CRITICAL`.

---

## 4. Risk Scoring Engine

SentinelAI calculates a holistic threat risk score on a scale from $0$ to $100$ for every alert and incident.

### Mathematical Formulation

$$\text{Risk Score} = (0.35 \times S_{\text{ML}}) + (0.30 \times S_{\text{Rule}}) + (0.20 \times S_{\text{Correlation}}) + (0.15 \times S_{\text{Intel}})$$

Where all component scores are normalized to $[0, 100]$:
- $S_{\text{ML}}$: Anomaly score from Isolation Forest (scaled $0-100$) weighted with Random Forest confidence.
- $S_{\text{Rule}}$: Severity weight of triggered detection rules:
  - Critical: $100$
  - High: $75$
  - Medium: $45$
  - Low: $20$
- $S_{\text{Correlation}}$: Number of linked events in the attack chain ($25 \text{ pts per correlated event}$, capped at $100$).
- $S_{\text{Intel}}$: Threat intelligence match confidence rating ($0$ if benign or unknown, $50-100$ for confirmed C2/malicious IOC).

### Severity Classification

| Score Range | Severity Tier | Recommended Analyst SLA |
| :---: | :---: | :--- |
| **$70 - 100$** | **CRITICAL** | Immediate response ($< 15$ minutes); isolate host or block IP. |
| **$50 - 69$** | **HIGH** | Urgent investigation ($< 1$ hour); containment review. |
| **$30 - 49$** | **MEDIUM** | Standard triage ($< 4$ hours); monitor activity. |
| **$0 - 29$** | **LOW** | Informational; logged for correlation or audit. |

### Explainability Output
Every alert stores a structured rationale breaking down the four components:
```json
{
  "rule_contribution": 22.5,
  "ml_contribution": 28.0,
  "correlation_contribution": 15.0,
  "intel_contribution": 15.0,
  "rationale": "High rule severity (75) + Anomaly score 0.80 + Multi-event chain + Matched C2 IOC 198.51.100.20"
}
```
