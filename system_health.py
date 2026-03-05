"""System Health Monitoring for Agent Stamina.

Monitors infrastructure health to prevent environmental failures
that can kill agents even when their cognitive stamina is fine.

Issue #2: System Health Monitoring — Track environment stamina
"""

import os
import json
import time
import subprocess
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path


@dataclass
class SystemHealthSnapshot:
    """A snapshot of system health metrics."""
    timestamp: datetime
    session_id: str
    
    # System metrics
    ram_percent: float  # 0-100
    ram_used_mb: float
    ram_total_mb: float
    disk_percent: float  # 0-100
    disk_free_gb: float
    
    # Browser metrics (if detectable)
    browser_memory_mb: Optional[float] = None
    browser_processes: int = 0
    
    # Gateway metrics
    gateway_responsive: bool = False
    gateway_latency_ms: Optional[float] = None
    
    # Derived status
    status: str = field(init=False)
    alerts: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        # Determine overall status
        critical_count = 0
        warning_count = 0
        self.alerts = []
        
        # RAM checks
        if self.ram_percent >= 90:
            critical_count += 1
            self.alerts.append(f"CRITICAL: RAM at {self.ram_percent:.1f}%")
        elif self.ram_percent >= 75:
            warning_count += 1
            self.alerts.append(f"WARNING: RAM at {self.ram_percent:.1f}%")
        
        # Disk checks
        if self.disk_percent >= 95:
            critical_count += 1
            self.alerts.append(f"CRITICAL: Disk at {self.disk_percent:.1f}%")
        elif self.disk_percent >= 85:
            warning_count += 1
            self.alerts.append(f"WARNING: Disk at {self.disk_percent:.1f}%")
        
        # Browser memory checks
        if self.browser_memory_mb and self.browser_memory_mb >= 1500:
            critical_count += 1
            self.alerts.append(f"CRITICAL: Browser using {self.browser_memory_mb:.0f}MB")
        elif self.browser_memory_mb and self.browser_memory_mb >= 800:
            warning_count += 1
            self.alerts.append(f"WARNING: Browser using {self.browser_memory_mb:.0f}MB")
        
        # Gateway checks
        if not self.gateway_responsive:
            critical_count += 1
            self.alerts.append("CRITICAL: Gateway unresponsive")
        elif self.gateway_latency_ms and self.gateway_latency_ms > 5000:
            warning_count += 1
            self.alerts.append(f"WARNING: Gateway slow ({self.gateway_latency_ms:.0f}ms)")
        
        # Overall status
        if critical_count > 0:
            self.status = "critical"
        elif warning_count > 0:
            self.status = "warning"
        else:
            self.status = "healthy"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'session_id': self.session_id,
            'ram_percent': self.ram_percent,
            'ram_used_mb': self.ram_used_mb,
            'ram_total_mb': self.ram_total_mb,
            'disk_percent': self.disk_percent,
            'disk_free_gb': self.disk_free_gb,
            'browser_memory_mb': self.browser_memory_mb,
            'browser_processes': self.browser_processes,
            'gateway_responsive': self.gateway_responsive,
            'gateway_latency_ms': self.gateway_latency_ms,
            'status': self.status,
            'alerts': self.alerts
        }


class SystemHealthMonitor:
    """Monitor system health to prevent infrastructure failures."""
    
    def __init__(self, session_id: str, db_path: str = ".agent_stamina.db"):
        self.session_id = session_id
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database for system health."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_health_snapshots (
                id INTEGER PRIMARY KEY,
                session_id TEXT,
                timestamp TEXT,
                ram_percent REAL,
                ram_used_mb REAL,
                ram_total_mb REAL,
                disk_percent REAL,
                disk_free_gb REAL,
                browser_memory_mb REAL,
                browser_processes INTEGER,
                gateway_responsive INTEGER,
                gateway_latency_ms REAL,
                status TEXT,
                alerts TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def _get_ram_usage(self) -> tuple[float, float, float]:
        """Get RAM usage (percent, used_mb, total_mb)."""
        try:
            # Try /proc/meminfo on Linux
            if os.path.exists('/proc/meminfo'):
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                
                total_kb = 0
                available_kb = 0
                
                for line in meminfo.split('\n'):
                    if line.startswith('MemTotal:'):
                        total_kb = int(line.split()[1])
                    elif line.startswith('MemAvailable:'):
                        available_kb = int(line.split()[1])
                
                if total_kb > 0:
                    used_kb = total_kb - available_kb
                    percent = (used_kb / total_kb) * 100
                    return percent, used_kb / 1024, total_kb / 1024
            
            # Fallback: try psutil if available
            try:
                import psutil
                mem = psutil.virtual_memory()
                return mem.percent, mem.used / (1024 * 1024), mem.total / (1024 * 1024)
            except ImportError:
                pass
            
            # Last resort: free command
            result = subprocess.run(['free', '-m'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('Mem:'):
                        parts = line.split()
                        total_mb = int(parts[1])
                        used_mb = int(parts[2])
                        percent = (used_mb / total_mb) * 100
                        return percent, used_mb, total_mb
        
        except Exception as e:
            pass
        
        return 0.0, 0.0, 0.0
    
    def _get_disk_usage(self) -> tuple[float, float]:
        """Get disk usage (percent, free_gb)."""
        try:
            # Try df command
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    # Parse percentage
                    percent_str = parts[4].replace('%', '')
                    percent = float(percent_str)
                    
                    # Parse available space
                    available_str = parts[3]
                    if available_str.endswith('G'):
                        free_gb = float(available_str[:-1])
                    elif available_str.endswith('T'):
                        free_gb = float(available_str[:-1]) * 1024
                    elif available_str.endswith('M'):
                        free_gb = float(available_str[:-1]) / 1024
                    else:
                        free_gb = 0.0
                    
                    return percent, free_gb
        
        except Exception:
            pass
        
        # Fallback: statvfs
        try:
            stat = os.statvfs('/')
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bavail * stat.f_frsize
            percent = ((total - free) / total) * 100 if total > 0 else 0
            free_gb = free / (1024 ** 3)
            return percent, free_gb
        except Exception:
            pass
        
        return 0.0, 0.0
    
    def _get_browser_memory(self) -> tuple[Optional[float], int]:
        """Get browser memory usage (total_mb, process_count)."""
        browsers = ['chrome', 'chromium', 'firefox', 'safari', 'edge', 'browser']
        total_mb = 0.0
        process_count = 0
        
        try:
            # Try ps command
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line_lower = line.lower()
                    for browser in browsers:
                        if browser in line_lower and 'grep' not in line_lower:
                            parts = line.split()
                            if len(parts) >= 6:
                                try:
                                    # RSS is in KB typically
                                    rss_kb = float(parts[5])
                                    total_mb += rss_kb / 1024
                                    process_count += 1
                                except (ValueError, IndexError):
                                    pass
                            break
        
        except Exception:
            pass
        
        if process_count > 0:
            return total_mb, process_count
        return None, 0
    
    def _check_gateway_health(self, timeout_sec: int = 2) -> tuple[bool, Optional[float]]:
        """Check OpenClaw gateway health."""
        try:
            start = time.time()
            result = subprocess.run(
                ['openclaw', 'gateway', 'status'],
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )
            elapsed = (time.time() - start) * 1000
            
            responsive = result.returncode == 0
            return responsive, elapsed if responsive else None
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False, None
        except Exception:
            return False, None
    
    def capture(self) -> SystemHealthSnapshot:
        """Capture a system health snapshot."""
        ram_pct, ram_used, ram_total = self._get_ram_usage()
        disk_pct, disk_free = self._get_disk_usage()
        browser_mem, browser_procs = self._get_browser_memory()
        gateway_ok, gateway_lat = self._check_gateway_health()
        
        snapshot = SystemHealthSnapshot(
            timestamp=datetime.now(),
            session_id=self.session_id,
            ram_percent=ram_pct,
            ram_used_mb=ram_used,
            ram_total_mb=ram_total,
            disk_percent=disk_pct,
            disk_free_gb=disk_free,
            browser_memory_mb=browser_mem,
            browser_processes=browser_procs,
            gateway_responsive=gateway_ok,
            gateway_latency_ms=gateway_lat
        )
        
        # Store in database
        self._store(snapshot)
        
        return snapshot
    
    def _store(self, snapshot: SystemHealthSnapshot):
        """Store snapshot in database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO system_health_snapshots 
            (session_id, timestamp, ram_percent, ram_used_mb, ram_total_mb,
             disk_percent, disk_free_gb, browser_memory_mb, browser_processes,
             gateway_responsive, gateway_latency_ms, status, alerts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.session_id,
            snapshot.timestamp.isoformat(),
            snapshot.ram_percent,
            snapshot.ram_used_mb,
            snapshot.ram_total_mb,
            snapshot.disk_percent,
            snapshot.disk_free_gb,
            snapshot.browser_memory_mb,
            snapshot.browser_processes,
            1 if snapshot.gateway_responsive else 0,
            snapshot.gateway_latency_ms,
            snapshot.status,
            json.dumps(snapshot.alerts)
        ))
        conn.commit()
        conn.close()
    
    def get_history(self, minutes: int = 60) -> List[SystemHealthSnapshot]:
        """Get system health history."""
        since = datetime.now() - timedelta(minutes=minutes)
        
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT timestamp, ram_percent, ram_used_mb, ram_total_mb,
                   disk_percent, disk_free_gb, browser_memory_mb, browser_processes,
                   gateway_responsive, gateway_latency_ms, status, alerts
            FROM system_health_snapshots
            WHERE session_id = ? AND timestamp > ?
            ORDER BY timestamp
        """, (self.session_id, since.isoformat())).fetchall()
        conn.close()
        
        snapshots = []
        for row in rows:
            snapshot = SystemHealthSnapshot(
                timestamp=datetime.fromisoformat(row[0]),
                session_id=self.session_id,
                ram_percent=row[1],
                ram_used_mb=row[2],
                ram_total_mb=row[3],
                disk_percent=row[4],
                disk_free_gb=row[5],
                browser_memory_mb=row[6],
                browser_processes=row[7],
                gateway_responsive=bool(row[8]),
                gateway_latency_ms=row[9]
            )
            snapshot.status = row[10]
            snapshot.alerts = json.loads(row[11]) if row[11] else []
            snapshots.append(snapshot)
        
        return snapshots
    
    def current_status(self) -> Optional[SystemHealthSnapshot]:
        """Get most recent system health snapshot."""
        history = self.get_history(minutes=999999)
        return history[-1] if history else None
    
    def should_alert(self) -> bool:
        """Check if any critical alerts are active."""
        status = self.current_status()
        if not status:
            return False
        return status.status == "critical"
    
    def get_alerts(self) -> List[str]:
        """Get current active alerts."""
        status = self.current_status()
        if not status:
            return []
        return status.alerts
    
    def health_score(self) -> float:
        """Calculate overall health score (0-100)."""
        status = self.current_status()
        if not status:
            return 100.0
        
        score = 100.0
        
        # Deduct for RAM
        if status.ram_percent >= 90:
            score -= 40
        elif status.ram_percent >= 75:
            score -= 20
        elif status.ram_percent >= 60:
            score -= 10
        
        # Deduct for disk
        if status.disk_percent >= 95:
            score -= 30
        elif status.disk_percent >= 85:
            score -= 15
        
        # Deduct for browser
        if status.browser_memory_mb:
            if status.browser_memory_mb >= 1500:
                score -= 20
            elif status.browser_memory_mb >= 800:
                score -= 10
        
        # Deduct for gateway
        if not status.gateway_responsive:
            score -= 50
        
        return max(0.0, score)


def quick_check(session_id: str = "system") -> SystemHealthSnapshot:
    """Quick system health check."""
    monitor = SystemHealthMonitor(session_id)
    return monitor.capture()


if __name__ == "__main__":
    # Demo
    print("=" * 60)
    print("System Health Monitor - Demo")
    print("=" * 60)
    
    snapshot = quick_check("demo-session")
    
    print(f"\n📊 System Health: {snapshot.status.upper()}")
    print(f"   Timestamp: {snapshot.timestamp}")
    print(f"\n💾 RAM: {snapshot.ram_percent:.1f}% ({snapshot.ram_used_mb:.0f}/{snapshot.ram_total_mb:.0f} MB)")
    print(f"💿 Disk: {snapshot.disk_percent:.1f}% full ({snapshot.disk_free_gb:.1f} GB free)")
    
    if snapshot.browser_memory_mb:
        print(f"🌐 Browser: {snapshot.browser_memory_mb:.0f} MB ({snapshot.browser_processes} processes)")
    else:
        print(f"🌐 Browser: Not detected")
    
    if snapshot.gateway_responsive:
        print(f"🦀 Gateway: ✅ Responsive ({snapshot.gateway_latency_ms:.1f}ms)")
    else:
        print(f"🦀 Gateway: 🔴 Unresponsive")
    
    if snapshot.alerts:
        print(f"\n⚠️  Alerts:")
        for alert in snapshot.alerts:
            print(f"   - {alert}")
    else:
        print(f"\n✅ No alerts")
    
    print("\n" + "=" * 60)
