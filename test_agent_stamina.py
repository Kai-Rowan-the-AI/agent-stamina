"""Tests for Agent Stamina components."""

import unittest
import sqlite3
import json
import os
import tempfile
from datetime import datetime

# Import modules to test
from stamina import StaminaMonitor, StaminaSnapshot
from system_health import SystemHealthMonitor, SystemHealthSnapshot, quick_check


class TestStaminaSnapshot(unittest.TestCase):
    """Test StaminaSnapshot dataclass."""
    
    def test_status_healthy(self):
        """Test healthy status detection."""
        snapshot = StaminaSnapshot(
            timestamp=datetime.now(),
            session_id="test",
            context_health=0.8,
            memory_freshness=0.9,
            error_rate=0.0,
            repetition_score=0.0
        )
        self.assertEqual(snapshot.status(), "healthy")
        self.assertGreater(snapshot.overall_score, 70)
    
    def test_status_critical(self):
        """Test critical status detection."""
        snapshot = StaminaSnapshot(
            timestamp=datetime.now(),
            session_id="test",
            context_health=0.05,
            memory_freshness=0.1,
            error_rate=0.5,
            repetition_score=0.3
        )
        self.assertEqual(snapshot.status(), "critical")


class TestStaminaMonitor(unittest.TestCase):
    """Test StaminaMonitor functionality."""
    
    def setUp(self):
        """Create temporary database."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self.monitor = StaminaMonitor("test-session", self.db_path)
    
    def tearDown(self):
        """Clean up."""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_record_and_retrieve(self):
        """Test recording and retrieving snapshots."""
        # Record a snapshot
        snapshot = self.monitor.record(
            context_health=0.8,
            memory_freshness=0.9,
            error_rate=0.05,
            repetition_score=0.1
        )
        
        # Verify it was stored
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.session_id, "test-session")
        
        # Retrieve history
        history = self.monitor.get_history(minutes=60)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].overall_score, snapshot.overall_score)
    
    def test_current_status(self):
        """Test getting current status."""
        # Initially no status
        self.assertIsNone(self.monitor.current_status())
        
        # Record and check
        self.monitor.record(context_health=0.8, memory_freshness=0.9, error_rate=0.05, repetition_score=0.1)
        current = self.monitor.current_status()
        self.assertIsNotNone(current)
        self.assertEqual(current.session_id, "test-session")


class TestSystemHealthMonitor(unittest.TestCase):
    """Test SystemHealthMonitor functionality."""
    
    def setUp(self):
        """Create temporary database."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self.monitor = SystemHealthMonitor("test-session", self.db_path)
    
    def tearDown(self):
        """Clean up."""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_capture(self):
        """Test capturing system health snapshot."""
        snapshot = self.monitor.capture()
        
        # Verify snapshot has required fields
        self.assertIsNotNone(snapshot.timestamp)
        self.assertEqual(snapshot.session_id, "test-session")
        self.assertIsInstance(snapshot.ram_percent, float)
        self.assertIsInstance(snapshot.disk_percent, float)
        self.assertIn(snapshot.status, ["healthy", "warning", "critical"])
    
    def test_health_score(self):
        """Test health score calculation."""
        # Capture initial state
        self.monitor.capture()
        score = self.monitor.health_score()
        
        # Score should be between 0 and 100
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)
    
    def test_database_storage(self):
        """Test that snapshots are stored in database."""
        self.monitor.capture()
        
        # Verify in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM system_health_snapshots")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 1)


class TestSystemHealthSnapshot(unittest.TestCase):
    """Test SystemHealthSnapshot dataclass."""
    
    def test_healthy_status(self):
        """Test healthy system status."""
        snapshot = SystemHealthSnapshot(
            timestamp=datetime.now(),
            session_id="test",
            ram_percent=40.0,
            ram_used_mb=4000,
            ram_total_mb=10000,
            disk_percent=50.0,
            disk_free_gb=100.0,
            gateway_responsive=True
        )
        self.assertEqual(snapshot.status, "healthy")
        self.assertEqual(len(snapshot.alerts), 0)
    
    def test_critical_ram(self):
        """Test critical RAM detection."""
        snapshot = SystemHealthSnapshot(
            timestamp=datetime.now(),
            session_id="test",
            ram_percent=95.0,
            ram_used_mb=9500,
            ram_total_mb=10000,
            disk_percent=50.0,
            disk_free_gb=100.0,
            gateway_responsive=True
        )
        self.assertEqual(snapshot.status, "critical")
        self.assertTrue(any("CRITICAL: RAM" in alert for alert in snapshot.alerts))
    
    def test_critical_gateway(self):
        """Test critical gateway detection."""
        snapshot = SystemHealthSnapshot(
            timestamp=datetime.now(),
            session_id="test",
            ram_percent=40.0,
            ram_used_mb=4000,
            ram_total_mb=10000,
            disk_percent=50.0,
            disk_free_gb=100.0,
            gateway_responsive=False
        )
        self.assertEqual(snapshot.status, "critical")
        self.assertTrue(any("Gateway unresponsive" in alert for alert in snapshot.alerts))


class TestPrometheusExporter(unittest.TestCase):
    """Test Prometheus exporter functionality."""
    
    def setUp(self):
        """Create temporary database with test data."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        
        # Initialize database with test data
        from stamina import StaminaMonitor
        monitor = StaminaMonitor("test-session", self.db_path)
        monitor.record(context_health=0.8, memory_freshness=0.9, error_rate=0.05, repetition_score=0.1)
        
        from system_health import SystemHealthMonitor
        sys_monitor = SystemHealthMonitor("test-session", self.db_path)
        sys_monitor.capture()
    
    def tearDown(self):
        """Clean up."""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_metrics_format(self):
        """Test Prometheus metrics format."""
        from prometheus_exporter import PrometheusExporter
        
        exporter = PrometheusExporter(self.db_path, port=9091)
        metrics = exporter._get_metrics()
        
        # Check for expected metric lines
        self.assertIn("# HELP agent_stamina_overall_score", metrics)
        self.assertIn("# TYPE agent_stamina_overall_score gauge", metrics)
        self.assertIn("agent_stamina_overall_score", metrics)
        
        # Check for system health metrics
        self.assertIn("agent_stamina_system_ram_percent", metrics)
        self.assertIn("agent_stamina_system_health_score", metrics)
    
    def test_metrics_include_session_label(self):
        """Test that metrics include session_id label."""
        from prometheus_exporter import PrometheusExporter
        
        exporter = PrometheusExporter(self.db_path, port=9091)
        metrics = exporter._get_metrics()
        
        # Should include session_id label
        self.assertIn('session_id="test-session"', metrics)


if __name__ == "__main__":
    unittest.main()
