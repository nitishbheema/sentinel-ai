import os
import time
import json
import uuid
import hmac
import hashlib
import requests
from typing import Dict, Any, List


class TelemetrySender:
    def __init__(self, backend_url: str, shared_secret: str, spool_file: str = "./agent_spool.json"):
        self.backend_url = backend_url
        self.shared_secret = shared_secret
        self.spool_file = spool_file
        self.session = requests.Session()

    def _build_auth_headers(self, payload_bytes: bytes) -> Dict[str, str]:
        timestamp = str(time.time())
        nonce = str(uuid.uuid4())
        message = f"{timestamp}:{nonce}:".encode("utf-8") + payload_bytes
        signature = hmac.new(
            self.shared_secret.encode("utf-8"),
            message,
            hashlib.sha256
        ).hexdigest()

        return {
            "Content-Type": "application/json",
            "X-Agent-Signature": signature,
            "X-Agent-Timestamp": timestamp,
            "X-Agent-Nonce": nonce,
            "X-Agent-Secret": self.shared_secret  # Backwards compatibility
        }

    def send_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Sends telemetry event to backend with HMAC-SHA256 signature and replay prevention headers;
        spools locally if connection fails.
        """
        try:
            payload_bytes = json.dumps(event_data, sort_keys=True).encode("utf-8")
            headers = self._build_auth_headers(payload_bytes)
            
            resp = self.session.post(
                self.backend_url,
                data=payload_bytes,
                headers=headers,
                timeout=5
            )
            if resp.status_code in [200, 201]:
                # Try flushing previously spooled events
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
        # Keep spool size bounded
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
                    payload_bytes = json.dumps(item, sort_keys=True).encode("utf-8")
                    headers = self._build_auth_headers(payload_bytes)
                    resp = self.session.post(
                        self.backend_url,
                        data=payload_bytes,
                        headers=headers,
                        timeout=3
                    )
                    if resp.status_code not in [200, 201]:
                        remaining.append(item)
                except Exception:
                    remaining.append(item)

            with open(self.spool_file, "w", encoding="utf-8") as f:
                json.dump(remaining, f)
        except Exception:
            pass
