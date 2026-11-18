import os
import psutil
from datetime import datetime, timezone
from typing import List, Dict, Any


class ProcessCollector:
    def __init__(self):
        self.seen_pids = set()
        # Initialize with currently running pids so we only report new spawns
        try:
            for p in psutil.process_iter(['pid']):
                self.seen_pids.add(p.info['pid'])
        except Exception:
            pass

    def collect(self) -> List[Dict[str, Any]]:
        new_events = []
        try:
            current_pids = set()
            for proc in psutil.process_iter(['pid', 'name', 'ppid', 'cmdline', 'username']):
                try:
                    pid = proc.info['pid']
                    current_pids.add(pid)
                    if pid not in self.seen_pids:
                        self.seen_pids.add(pid)
                        parent_name = "unknown"
                        ppid = proc.info.get('ppid')
                        if ppid:
                            try:
                                parent = psutil.Process(ppid)
                                parent_name = parent.name()
                            except Exception:
                                pass

                        new_events.append({
                            "event_type": "process_spawn",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "process_name": proc.info.get('name'),
                            "pid": pid,
                            "parent_pid": ppid,
                            "username": proc.info.get('username'),
                            "details": {
                                "parent_process": parent_name,
                                "cmdline": " ".join(proc.info.get('cmdline') or [])[:200]
                            }
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"[ProcessCollector] Error: {e}")

        return new_events
