# SentinelAI Database Schema Documentation

SentinelAI utilizes PostgreSQL (with SQLite compatibility for offline laboratory testing) orchestrated via SQLAlchemy ORM and Alembic schema migrations.

---

## Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    users ||--o{ incidents : "assigned_to"
    users ||--o{ incident_notes : "author"
    users ||--o{ audit_logs : "performed_by"
    users ||--o{ response_actions : "approved_by"

    endpoints ||--o{ agents : "monitored_by"

    events ||--o{ predictions : "evaluated_by"
    events ||--o{ alerts : "triggered_by"
    events ||--o{ incident_events : "linked_to"

    detection_rules ||--o{ alerts : "generates"

    incidents ||--o{ incident_events : "contains"
    incidents ||--o{ incident_notes : "annotated_with"
    incidents ||--o{ response_actions : "recommends"

    alerts ||--o{ response_actions : "associates"

    users {
        int id PK
        string username UK
        string email UK
        string hashed_password
        string role
        boolean is_active
        int failed_login_attempts
        datetime locked_until
        datetime created_at
        datetime updated_at
    }

    endpoints {
        int id PK
        string hostname UK
        string ip_address
        string os_type
        string os_version
        string status
        string agent_version
        datetime last_seen
        boolean isolation_status
        json meta_info
        datetime created_at
    }

    agents {
        int id PK
        int endpoint_id FK
        string agent_type
        string status
        string version
        string api_key_hash
        datetime last_heartbeat
        datetime created_at
    }

    events {
        int id PK
        string event_uuid UK
        string event_source
        string event_type
        datetime timestamp
        string source_ip
        int source_port
        string destination_ip
        int destination_port
        string protocol
        string host_id
        string username
        string process_name
        int process_pid
        json raw_data
        json normalized_data
        string hash_checksum
        datetime created_at
    }

    predictions {
        int id PK
        int event_id FK
        string model_name
        string model_version
        string prediction_label
        float confidence
        float anomaly_score
        json feature_contributions
        datetime created_at
    }

    detection_rules {
        int id PK
        string rule_id UK
        string name
        text description
        string severity
        string category
        text condition_yaml
        boolean is_enabled
        int time_window_seconds
        int threshold
        string mitre_technique_id
        string version
        datetime created_at
        datetime updated_at
    }

    alerts {
        int id PK
        string alert_uuid UK
        string title
        text description
        string severity
        string status
        string source
        int rule_id FK
        int event_id FK
        int ml_prediction_id FK
        float risk_score
        json risk_breakdown
        string mitre_technique
        json evidence
        datetime created_at
        datetime updated_at
    }

    incidents {
        int id PK
        string incident_uuid UK
        string title
        text description
        string severity
        string status
        int assigned_to_user_id FK
        float risk_score
        json mitre_tactics
        datetime created_at
        datetime updated_at
    }

    incident_events {
        int id PK
        int incident_id FK
        int event_id FK
        datetime added_at
    }

    incident_notes {
        int id PK
        int incident_id FK
        int user_id FK
        text note
        datetime created_at
    }

    response_actions {
        int id PK
        string action_uuid UK
        int incident_id FK
        int alert_id FK
        string action_type
        string target
        string status
        int requested_by_user_id FK
        int approved_by_user_id FK
        json execution_result
        boolean rollback_available
        datetime created_at
        datetime updated_at
    }

    threat_indicators {
        int id PK
        string indicator_type
        string value UK
        string threat_type
        string severity
        int confidence
        string source
        boolean is_active
        datetime expires_at
        datetime created_at
    }

    audit_logs {
        int id PK
        int user_id FK
        string action
        string target_type
        string target_id
        json details
        string ip_address
        datetime timestamp
    }
```

---

## Table Descriptions

1. **`users`**: Platform analysts and administrators. Passwords hashed with Argon2/bcrypt. Supports failed login counter and lockout expiration.
2. **`endpoints`**: Fleet hosts registered for agent telemetry and quarantine tracking.
3. **`agents`**: Installed sensor agents with heartbeat monitoring and API keys.
4. **`events`**: Canonical security telemetry repository with deduplication hashes.
5. **`predictions`**: Supervised and unsupervised inference output associated with each event.
6. **`detection_rules`**: Sigma-inspired YAML heuristics and sliding threshold configurations.
7. **`alerts`**: High-priority security warnings with explainable risk breakdown.
8. **`incidents`**: Multi-stage correlated security investigations.
9. **`incident_events`**: Cross-reference mapping between incidents and linked telemetry events.
10. **`incident_notes`**: Analyst workbench log notes and hypothesis tracking.
11. **`response_actions`**: Approval-controlled defensive actions (IP block, host quarantine).
12. **`threat_indicators`**: Locally maintained indicators of compromise (IOCs).
13. **`audit_logs`**: Immutable audit trails recording analyst actions and system modifications.
