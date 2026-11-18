import os
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any


class FileIntegrityCollector:
    def __init__(self, monitored_paths: List[str] = None):
        self.monitored_paths = monitored_paths or ["/etc/passwd", "/etc/hosts"]
        self.file_hashes = {}
        for p in self.monitored_paths:
            if os.path.exists(p):
                self.file_hashes[p] = self._calc_hash(p)

    def _calc_hash(self, path: str) -> str:
        try:
            with open(path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    def collect(self) -> List[Dict[str, Any]]:
        events = []
        for path in self.monitored_paths:
            if os.path.exists(path):
                current_hash = self._calc_hash(path)
                prev_hash = self.file_hashes.get(path)
                if prev_hash and current_hash != prev_hash:
                    self.file_hashes[path] = current_hash
                    events.append({
                        "event_type": "file_mod",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "details": {
                            "file_path": path,
                            "old_hash": prev_hash,
                            "new_hash": current_hash,
                            "action": "MODIFIED"
                        }
                    })
                elif not prev_hash:
                    self.file_hashes[path] = current_hash

        return events
