import os
import json
import requests
from typing import Dict, Any


class SuricataCollector:
    def __init__(self, eve_path: str = "sample_eve.json", backend_url: str = "http://127.0.0.1:8000/api/v1/events/ingest/suricata"):
        self.eve_path = eve_path
        self.backend_url = backend_url
        self.last_pos = 0

    def read_and_ingest(self) -> int:
        if not os.path.exists(self.eve_path):
            return 0

        ingested = 0
        with open(self.eve_path, "r", encoding="utf-8") as f:
            f.seek(self.last_pos)
            lines = f.readlines()
            self.last_pos = f.tell()

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                # Only ingest alert events or flow events
                if data.get("event_type") == "alert" or "alert" in data:
                    secret = os.environ.get("SENTINEL_AGENT_SECRET", "")
                    headers = {"Content-Type": "application/json"}
                    if secret:
                        headers["X-Agent-Secret"] = secret
                    resp = requests.post(
                        self.backend_url,
                        json=data,
                        headers=headers,
                        timeout=3
                    )
                    if resp.status_code in [200, 201]:
                        ingested += 1
            except Exception as e:
                print(f"[SuricataCollector] Ingest error: {e}")

        return ingested


if __name__ == "__main__":
    col = SuricataCollector()
    c = col.read_and_ingest()
    print(f"[SuricataCollector] Ingested {c} Suricata alerts.")
