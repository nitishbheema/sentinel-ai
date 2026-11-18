import os
import re
from datetime import datetime, timezone
from typing import List, Dict, Any


class AuthCollector:
    def __init__(self, log_path: str = "/var/log/auth.log"):
        self.log_path = log_path
        self.last_position = 0

    def collect(self) -> List[Dict[str, Any]]:
        events = []
        if not os.path.exists(self.log_path):
            return events

        try:
            with open(self.log_path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(self.last_position)
                lines = f.readlines()
                self.last_position = f.tell()

            for line in lines:
                event = self._parse_line(line)
                if event:
                    events.append(event)
        except Exception as e:
            print(f"[AuthCollector] Read error: {e}")

        return events

    def _parse_line(self, line: str) -> Dict[str, Any]:
        # Failed password detection
        fail_match = re.search(r"Failed password for (invalid user )?(\S+) from (\S+) port (\d+)", line)
        if fail_match:
            username = fail_match.group(2)
            src_ip = fail_match.group(3)
            src_port = int(fail_match.group(4))
            return {
                "event_type": "auth_failure",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "username": username,
                "ip_address": src_ip,
                "details": {
                    "source_port": src_port,
                    "service": "sshd",
                    "reason": "Invalid credentials"
                }
            }

        # Accepted password detection
        succ_match = re.search(r"Accepted password for (\S+) from (\S+) port (\d+)", line)
        if succ_match:
            username = succ_match.group(1)
            src_ip = succ_match.group(2)
            src_port = int(succ_match.group(3))
            return {
                "event_type": "auth_success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "username": username,
                "ip_address": src_ip,
                "details": {
                    "source_port": src_port,
                    "service": "sshd"
                }
            }

        return None
