import os
import json
import time
import requests
from typing import List, Dict, Any


class ZeekCollector:
    def __init__(self, log_path: str = "sample_conn.log", backend_url: str = "http://127.0.0.1:8000/api/v1/events/ingest/zeek"):
        self.log_path = log_path
        self.backend_url = backend_url
        self.last_pos = 0

    def parse_line(self, line: str) -> Dict[str, Any]:
        line = line.strip()
        if not line or line.startswith("#"):
            return None

        # Check if line is JSON
        if line.startswith("{"):
            try:
                return json.loads(line)
            except Exception:
                pass

        # Parse standard Zeek tab-delimited conn.log
        parts = line.split("\t")
        if len(parts) >= 10:
            try:
                return {
                    "ts": float(parts[0]),
                    "uid": parts[1],
                    "id_orig_h": parts[2],
                    "id_orig_p": int(parts[3]),
                    "id_resp_h": parts[4],
                    "id_resp_p": int(parts[5]),
                    "proto": parts[6],
                    "service": parts[7] if parts[7] != "-" else "unknown",
                    "duration": float(parts[8]) if parts[8] != "-" else 0.0,
                    "orig_bytes": int(parts[9]) if parts[9] != "-" else 0,
                    "resp_bytes": int(parts[10]) if len(parts) > 10 and parts[10] != "-" else 0,
                    "conn_state": parts[11] if len(parts) > 11 else "SF"
                }
            except Exception:
                return None
        return None

    def read_and_ingest(self) -> int:
        if not os.path.exists(self.log_path):
            return 0

        ingested = 0
        with open(self.log_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(self.last_pos)
            lines = f.readlines()
            self.last_pos = f.tell()

        for line in lines:
            event = self.parse_line(line)
            if event:
                try:
                    resp = requests.post(
                        self.backend_url,
                        json=event,
                        headers={"X-Agent-Secret": "sentinel_agent_telemetry_secure_key_2026"},
                        timeout=3
                    )
                    if resp.status_code in [200, 201]:
                        ingested += 1
                except Exception as e:
                    print(f"[ZeekCollector] Connection error: {e}")

        return ingested


if __name__ == "__main__":
    col = ZeekCollector()
    count = col.read_and_ingest()
    print(f"[ZeekCollector] Processed and sent {count} logs.")
