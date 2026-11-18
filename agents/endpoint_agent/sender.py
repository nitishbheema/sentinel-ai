import os
import time
import json
import requests
from typing import Dict, Any, List


class TelemetrySender:
    def __init__(self, backend_url: str, shared_secret: str, spool_file: str = "./agent_spool.json"):
        self.backend_url = backend_url
        self.shared_secret = shared_secret
        self.spool_file = spool_file
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-Agent-Secret": self.shared_secret
        })

    def send_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Sends telemetry event to backend; spools locally if connection fails
        """
        try:
            resp = self.session.post(self.backend_url, json=event_data, timeout=5)
            if resp.status_code in [200, 201]:
                # Try flushing any previously spooled events
                self.flush_spool()
                return True
            else:
                print(f"[TelemetrySender] Server returned {resp.status_code}: {resp.text}")
                self._spool_event(event_data)
                return False
        except requests.exceptions.RequestException as e:
            print(f"[TelemetrySender] Network error: {e}. Spooling event locally.")
            self._spool_event(event_data)
            return False

    def _spool_event(self, event_data: Dict[str, Any]):
        spooled = []
        if os.path.exists(self.spool_file):
            try:
                with open(self.spool_file, "r", encoding="utf-8") as f:
                    spooled = json.load(f)
            except Exception:
                spooled = []
        spooled.append(event_data)
        # Keep spool size reasonable
        spooled = spooled[-500:]
        try:
            with open(self.spool_file, "w", encoding="utf-8") as f:
                json.dump(spooled, f)
        except Exception as e:
            print(f"[TelemetrySender] Error saving spool: {e}")

    def flush_spool(self):
        if not os.path.exists(self.spool_file):
            return
        try:
            with open(self.spool_file, "r", encoding="utf-8") as f:
                spooled = json.load(f)
            if not spooled:
                return

            remaining = []
            for item in spooled:
                try:
                    resp = self.session.post(self.backend_url, json=item, timeout=3)
                    if resp.status_code not in [200, 201]:
                        remaining.append(item)
                except Exception:
                    remaining.append(item)

            with open(self.spool_file, "w", encoding="utf-8") as f:
                json.dump(remaining, f)
        except Exception:
            pass
