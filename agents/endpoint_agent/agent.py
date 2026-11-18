import os
import sys
import time
import socket
import yaml
from datetime import datetime, timezone

from collectors.auth_collector import AuthCollector
from collectors.process_collector import ProcessCollector
from collectors.network_collector import NetworkCollector
from collectors.file_collector import FileIntegrityCollector
from sender import TelemetrySender


class EndpointAgent:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.hostname = self.config.get("agent", {}).get("hostname", socket.gethostname())
        self.ip_address = self._get_local_ip()
        
        backend_url = self.config.get("agent", {}).get("backend_url", "http://127.0.0.1:8000/api/v1/events/ingest/endpoint")
        secret = self.config.get("agent", {}).get("shared_secret", "sentinel_agent_telemetry_secure_key_2026")
        self.sender = TelemetrySender(backend_url, secret)

        # Initialize collectors
        self.auth_col = AuthCollector()
        self.proc_col = ProcessCollector()
        self.net_col = NetworkCollector(self.config.get("collectors", {}).get("network", {}).get("suspicious_ports"))
        self.file_col = FileIntegrityCollector(self.config.get("collectors", {}).get("file_integrity", {}).get("monitored_paths"))

    def _load_config(self, path: str) -> dict:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def run_once(self):
        # 1. Process events
        for pe in self.proc_col.collect():
            pe["hostname"] = self.hostname
            pe["ip_address"] = self.ip_address
            self.sender.send_event(pe)

        # 2. Auth events
        for ae in self.auth_col.collect():
            ae["hostname"] = self.hostname
            self.sender.send_event(ae)

        # 3. Network events
        for ne in self.net_col.collect():
            ne["hostname"] = self.hostname
            self.sender.send_event(ne)

        # 4. File integrity events
        for fe in self.file_col.collect():
            fe["hostname"] = self.hostname
            fe["ip_address"] = self.ip_address
            self.sender.send_event(fe)

    def start(self, interval: int = 10):
        print(f"[SentinelAgent] Agent active on host '{self.hostname}' ({self.ip_address}). Ingesting telemetry...")
        while True:
            try:
                self.run_once()
                time.sleep(interval)
            except KeyboardInterrupt:
                print("[SentinelAgent] Stopped by user.")
                break
            except Exception as e:
                print(f"[SentinelAgent] Runtime exception: {e}")
                time.sleep(interval)


if __name__ == "__main__":
    agent = EndpointAgent()
    agent.start()
