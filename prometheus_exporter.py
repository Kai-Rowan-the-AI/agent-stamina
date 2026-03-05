"""Prometheus metrics exporter for Agent Stamina.

Provides a /metrics endpoint compatible with Prometheus scraping.

Issue #1: Prometheus /metrics endpoint
"""

import sqlite3
import json
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, List, Dict, Any
from threading import Thread


class PrometheusExporter:
    """Prometheus-compatible metrics exporter for Agent Stamina."""
    
    def __init__(self, db_path: str = ".agent_stamina.db", port: int = 9090):
        self.db_path = db_path
        self.port = port
        self.server: Optional[HTTPServer] = None
        self._running = False
    
    def _get_metrics(self) -> str:
        """Generate Prometheus exposition format metrics."""
        lines: List[str] = []
        
        # Help and type annotations
        lines.append("# HELP agent_stamina_overall_score Overall stamina score (0-100)")
        lines.append("# TYPE agent_stamina_overall_score gauge")
        
        lines.append("# HELP agent_stamina_context_health Context health percentage (0-1)")
        lines.append("# TYPE agent_stamina_context_health gauge")
        
        lines.append("# HELP agent_stamina_memory_freshness Memory freshness percentage (0-1)")
        lines.append("# TYPE agent_stamina_memory_freshness gauge")
        
        lines.append("# HELP agent_stamina_error_rate Error rate (0-1)")
        lines.append("# TYPE agent_stamina_error_rate gauge")
        
        lines.append("# HELP agent_stamina_repetition_score Repetition detection score (0-1)")
        lines.append("# TYPE agent_stamina_repetition_score gauge")
        
        lines.append("# HELP agent_stamina_snapshots_total Total number of snapshots recorded")
        lines.append("# TYPE agent_stamina_snapshots_total counter")
        
        lines.append("# HELP agent_stamina_session_runtime_seconds Total session runtime")
        lines.append("# TYPE agent_stamina_session_runtime_seconds counter")
        
        # System health metrics
        lines.append("# HELP agent_stamina_system_ram_percent System RAM usage percent")
        lines.append("# TYPE agent_stamina_system_ram_percent gauge")
        
        lines.append("# HELP agent_stamina_system_disk_percent System disk usage percent")
        lines.append("# TYPE agent_stamina_system_disk_percent gauge")
        
        lines.append("# HELP agent_stamina_system_browser_memory_mb Browser memory usage in MB")
        lines.append("# TYPE agent_stamina_system_browser_memory_mb gauge")
        
        lines.append("# HELP agent_stamina_system_gateway_responsive Gateway responsiveness (1=up, 0=down)")
        lines.append("# TYPE agent_stamina_system_gateway_responsive gauge")
        
        lines.append("# HELP agent_stamina_system_health_score Overall system health score (0-100)")
        lines.append("# TYPE agent_stamina_system_health_score gauge")
        
        # Fetch data from database
        conn = sqlite3.connect(self.db_path)
        
        # Get latest stamina snapshots per session
        cursor = conn.execute("""
            SELECT s1.session_id, s1.overall_score, s1.context_health, 
                   s1.memory_freshness, s1.error_rate, s1.repetition_score,
                   s1.timestamp
            FROM stamina_snapshots s1
            INNER JOIN (
                SELECT session_id, MAX(timestamp) as max_ts
                FROM stamina_snapshots
                GROUP BY session_id
            ) s2 ON s1.session_id = s2.session_id AND s1.timestamp = s2.max_ts
        """)
        
        stamina_rows = cursor.fetchall()
        
        # Get snapshot counts per session
        cursor = conn.execute("""
            SELECT session_id, COUNT(*) as count
            FROM stamina_snapshots
            GROUP BY session_id
        """)
        snapshot_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get runtime per session
        cursor = conn.execute("""
            SELECT session_id, 
                   MIN(timestamp) as start_time,
                   MAX(timestamp) as last_time
            FROM stamina_snapshots
            GROUP BY session_id
        """)
        
        runtimes = {}
        for row in cursor.fetchall():
            session_id, start_str, last_str = row
            try:
                start = datetime.fromisoformat(start_str)
                last = datetime.fromisoformat(last_str)
                runtime = (last - start).total_seconds()
                runtimes[session_id] = runtime
            except:
                runtimes[session_id] = 0
        
        # Get latest system health snapshots
        cursor = conn.execute("""
            SELECT s1.session_id, s1.ram_percent, s1.disk_percent,
                   s1.browser_memory_mb, s1.gateway_responsive
            FROM system_health_snapshots s1
            INNER JOIN (
                SELECT session_id, MAX(timestamp) as max_ts
                FROM system_health_snapshots
                GROUP BY session_id
            ) s2 ON s1.session_id = s2.session_id AND s1.timestamp = s2.max_ts
        """)
        
        system_rows = cursor.fetchall()
        conn.close()
        
        # Output stamina metrics
        for row in stamina_rows:
            session_id, score, ctx, mem, err, rep, ts = row
            session_label = f'session_id="{session_id}"'
            
            lines.append(f'agent_stamina_overall_score{{{session_label}}} {score}')
            lines.append(f'agent_stamina_context_health{{{session_label}}} {ctx}')
            lines.append(f'agent_stamina_memory_freshness{{{session_label}}} {mem}')
            lines.append(f'agent_stamina_error_rate{{{session_label}}} {err}')
            lines.append(f'agent_stamina_repetition_score{{{session_label}}} {rep}')
        
        # Output snapshot counts
        for session_id, count in snapshot_counts.items():
            session_label = f'session_id="{session_id}"'
            lines.append(f'agent_stamina_snapshots_total{{{session_label}}} {count}')
        
        # Output runtimes
        for session_id, runtime in runtimes.items():
            session_label = f'session_id="{session_id}"'
            lines.append(f'agent_stamina_session_runtime_seconds{{{session_label}}} {runtime}')
        
        # Output system health metrics
        for row in system_rows:
            session_id, ram_pct, disk_pct, browser_mem, gateway_ok = row
            session_label = f'session_id="{session_id}"'
            
            lines.append(f'agent_stamina_system_ram_percent{{{session_label}}} {ram_pct}')
            lines.append(f'agent_stamina_system_disk_percent{{{session_label}}} {disk_pct}')
            
            if browser_mem is not None:
                lines.append(f'agent_stamina_system_browser_memory_mb{{{session_label}}} {browser_mem}')
            
            gateway_val = 1 if gateway_ok else 0
            lines.append(f'agent_stamina_system_gateway_responsive{{{session_label}}} {gateway_val}')
            
            # Calculate health score
            health_score = 100.0
            if ram_pct >= 90:
                health_score -= 40
            elif ram_pct >= 75:
                health_score -= 20
            
            if disk_pct >= 95:
                health_score -= 30
            elif disk_pct >= 85:
                health_score -= 15
            
            if browser_mem and browser_mem >= 1500:
                health_score -= 20
            elif browser_mem and browser_mem >= 800:
                health_score -= 10
            
            if not gateway_ok:
                health_score -= 50
            
            health_score = max(0.0, health_score)
            lines.append(f'agent_stamina_system_health_score{{{session_label}}} {health_score}')
        
        return '\n'.join(lines) + '\n'
    
    def start(self, blocking: bool = False):
        """Start the metrics server."""
        
        class MetricsHandler(BaseHTTPRequestHandler):
            exporter = self
            
            def do_GET(self):
                if self.path == '/metrics':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain; version=0.0.4')
                    self.end_headers()
                    metrics = self.exporter._get_metrics()
                    self.wfile.write(metrics.encode())
                elif self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "healthy"}).encode())
                elif self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html')
                    self.end_headers()
                    html = """
                    <html><body>
                    <h1>Agent Stamina Metrics</h1>
                    <p><a href="/metrics">Prometheus Metrics</a></p>
                    <p><a href="/health">Health Check</a></p>
                    </body></html>
                    """
                    self.wfile.write(html.encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                # Suppress default logging
                pass
        
        self.server = HTTPServer(('', self.port), MetricsHandler)
        self._running = True
        
        print(f"📊 Prometheus metrics server started on port {self.port}")
        print(f"   Endpoint: http://localhost:{self.port}/metrics")
        print(f"   Health:   http://localhost:{self.port}/health")
        
        if blocking:
            self.server.serve_forever()
        else:
            self._thread = Thread(target=self.server.serve_forever, daemon=True)
            self._thread.start()
    
    def stop(self):
        """Stop the metrics server."""
        if self.server:
            self.server.shutdown()
            self._running = False
            print("📊 Prometheus metrics server stopped")


def serve_metrics(db_path: str = ".agent_stamina.db", port: int = 9090):
    """Start metrics server (blocking)."""
    exporter = PrometheusExporter(db_path, port)
    exporter.start(blocking=True)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Stamina Prometheus Exporter")
    parser.add_argument("--port", type=int, default=9090, help="Port to serve metrics on")
    parser.add_argument("--db", default=".agent_stamina.db", help="Path to stamina database")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Agent Stamina - Prometheus Metrics Exporter")
    print("=" * 60)
    print()
    
    serve_metrics(args.db, args.port)
