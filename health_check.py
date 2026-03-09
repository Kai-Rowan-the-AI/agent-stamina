#!/usr/bin/env python3
"""Health check endpoint for Agent Stamina.

Provides liveness and readiness probes for Kubernetes deployments.

Usage:
    python3 health_check.py                    # Run server on port 8081
    python3 health_check.py --port 8081        # Run server on custom port
    python3 health_check.py --check            # One-shot check, exit 0/1
"""

import argparse
import json
import sqlite3
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional
from datetime import datetime, timedelta


class HealthChecker:
    """Health checker for Agent Stamina."""
    
    def __init__(self, db_path: str = ".agent_stamina.db"):
        self.db_path = db_path
    
    def check_liveness(self) -> tuple[bool, dict]:
        """Check if the service is alive (basic check)."""
        return True, {
            "status": "alive",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "can_access_db_file": self._can_access_db()
            }
        }
    
    def check_readiness(self) -> tuple[bool, dict]:
        """Check if the service is ready to serve requests."""
        checks = {}
        
        # Check database accessibility
        db_ok = self._check_db_connection()
        checks["database_connection"] = "ok" if db_ok else "failed"
        
        # Check recent data (within last 30 minutes)
        recent_data_ok = self._check_recent_data()
        checks["recent_data"] = "ok" if recent_data_ok else "no_recent_data"
        
        # Check disk space
        disk_ok, disk_free = self._check_disk_space()
        checks["disk_space"] = f"{disk_free:.1f}GB free" if disk_ok else "low"
        
        all_ok = db_ok and recent_data_ok and disk_ok
        
        return all_ok, {
            "status": "ready" if all_ok else "not_ready",
            "timestamp": datetime.now().isoformat(),
            "checks": checks
        }
    
    def check_startup(self) -> tuple[bool, dict]:
        """Check if the service has started correctly."""
        checks = {}
        
        # Check database file exists and is writable
        db_exists = self._can_access_db()
        checks["database_accessible"] = db_exists
        
        # Check schema is initialized
        schema_ok = self._check_schema()
        checks["schema_initialized"] = schema_ok
        
        all_ok = db_exists and schema_ok
        
        return all_ok, {
            "status": "started" if all_ok else "starting",
            "timestamp": datetime.now().isoformat(),
            "checks": checks
        }
    
    def _can_access_db(self) -> bool:
        """Check if database file is accessible."""
        import os
        return os.path.exists(self.db_path) and os.access(self.db_path, os.R_OK)
    
    def _check_db_connection(self) -> bool:
        """Check if database connection works."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            conn.execute("SELECT 1")
            conn.close()
            return True
        except:
            return False
    
    def _check_recent_data(self, minutes: int = 30) -> bool:
        """Check if there's recent data in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            since = (datetime.now() - timedelta(minutes=minutes)).isoformat()
            
            # Check stamina snapshots
            cursor = conn.execute(
                "SELECT COUNT(*) FROM stamina_snapshots WHERE timestamp > ?",
                (since,)
            )
            stamina_count = cursor.fetchone()[0]
            
            conn.close()
            return stamina_count > 0
        except:
            return False
    
    def _check_disk_space(self, min_free_gb: float = 1.0) -> tuple[bool, float]:
        """Check if there's enough disk space."""
        try:
            import shutil
            stat = shutil.disk_usage('/')
            free_gb = stat.free / (1024 ** 3)
            return free_gb >= min_free_gb, free_gb
        except:
            return False, 0.0
    
    def _check_schema(self) -> bool:
        """Check if database schema is initialized."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='stamina_snapshots'"
            )
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except:
            return False


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoints."""
    
    checker: Optional[HealthChecker] = None
    
    def do_GET(self):
        if self.path == "/health/live" or self.path == "/healthz":
            self._send_health_response(*self.checker.check_liveness())
        elif self.path == "/health/ready":
            self._send_health_response(*self.checker.check_readiness())
        elif self.path == "/health/startup":
            self._send_health_response(*self.checker.check_startup())
        elif self.path == "/health":
            # Combined health check
            live_ok, live_data = self.checker.check_liveness()
            ready_ok, ready_data = self.checker.check_readiness()
            
            all_ok = live_ok and ready_ok
            combined = {
                "status": "healthy" if all_ok else "unhealthy",
                "liveness": live_data,
                "readiness": ready_data
            }
            self._send_json_response(200 if all_ok else 503, combined)
        else:
            self.send_response(404)
            self.end_headers()
    
    def _send_health_response(self, healthy: bool, data: dict):
        """Send health check response."""
        status_code = 200 if healthy else 503
        self._send_json_response(status_code, data)
    
    def _send_json_response(self, status_code: int, data: dict):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run_server(port: int = 8081, db_path: str = ".agent_stamina.db"):
    """Run the health check server."""
    checker = HealthChecker(db_path)
    HealthHandler.checker = checker
    
    server = HTTPServer(('', port), HealthHandler)
    
    print(f"🩺 Health check server started on port {port}")
    print(f"   Endpoints:")
    print(f"   - GET /health/live    (liveness probe)")
    print(f"   - GET /health/ready   (readiness probe)")
    print(f"   - GET /health/startup (startup probe)")
    print(f"   - GET /health         (combined)")
    print(f"   - GET /healthz        (Kubernetes compatible)")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Health check server stopped")


def one_shot_check(db_path: str = ".agent_stamina.db") -> bool:
    """Run a one-shot health check."""
    checker = HealthChecker(db_path)
    
    live_ok, live_data = checker.check_liveness()
    ready_ok, ready_data = checker.check_readiness()
    
    all_ok = live_ok and ready_ok
    
    print(json.dumps({
        "healthy": all_ok,
        "liveness": live_data,
        "readiness": ready_data
    }, indent=2))
    
    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent Stamina Health Check")
    parser.add_argument("--port", type=int, default=8081, help="Port to serve on")
    parser.add_argument("--db", default=".agent_stamina.db", help="Database path")
    parser.add_argument("--check", action="store_true", help="One-shot check (exit 0/1)")
    
    args = parser.parse_args()
    
    if args.check:
        healthy = one_shot_check(args.db)
        sys.exit(0 if healthy else 1)
    else:
        run_server(args.port, args.db)
