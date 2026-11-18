import psutil
from datetime import datetime, timezone
from typing import List, Dict, Any


class NetworkCollector:
    def __init__(self, suspicious_ports: List[int] = None):
        self.suspicious_ports = set(suspicious_ports or [4444, 5555, 6667, 8888, 9999, 1337, 31337])
        self.seen_connections = set()

    def collect(self) -> List[Dict[str, Any]]:
        events = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == psutil.CONN_ESTABLISHED and conn.raddr:
                    dst_ip, dst_port = conn.raddr.ip, conn.raddr.port
                    src_ip, src_port = conn.laddr.ip, conn.laddr.port
                    conn_key = f"{src_ip}:{src_port}->{dst_ip}:{dst_port}"

                    if conn_key not in self.seen_connections:
                        self.seen_connections.add(conn_key)
                        is_suspicious = dst_port in self.suspicious_ports or dst_port > 30000

                        events.append({
                            "event_type": "network_conn",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "ip_address": src_ip,
                            "details": {
                                "source_port": src_port,
                                "destination_ip": dst_ip,
                                "destination_port": dst_port,
                                "status": conn.status,
                                "pid": conn.pid,
                                "is_suspicious": is_suspicious
                            }
                        })
        except Exception as e:
            # Network connection inspection can require admin rights on some hosts
            pass

        return events
