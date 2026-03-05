"""Easy self-monitoring for OpenClaw agents.

Drop-in monitoring for agents running in OpenClaw environment.

Usage:
    from openclaw_easy import monitor_me, stamina_snapshot
    
    # One-liner at start of your agent session
    tracker = monitor_me()
    
    # Or record snapshots throughout your work
    stamina_snapshot()  # Records current state
    
    # In long-running tasks, check periodically
    if should_checkpoint():
        print("Time to save progress!")
"""

import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from functools import wraps

# Try to import from local modules
try:
    from stamina import StaminaMonitor
    from openclaw_integration import OpenClawStamina
except ImportError:
    # Fallback: assume we're in the same directory
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from stamina import StaminaMonitor
    from openclaw_integration import OpenClawStamina


# Global tracker instance for easy access
_tracker: Optional[OpenClawStamina] = None
_start_time: Optional[datetime] = None


def monitor_me(session_id: Optional[str] = None, 
               auto_record: bool = True,
               verbose: bool = True) -> OpenClawStamina:
    """Start monitoring this agent session.
    
    Args:
        session_id: Optional custom session ID (auto-generated if not provided)
        auto_record: Whether to record initial snapshot
        verbose: Print status to console
        
    Returns:
        OpenClawStamina tracker instance
    """
    global _tracker, _start_time
    
    _start_time = datetime.now()
    _tracker = OpenClawStamina()
    
    # Override session ID if provided
    if session_id:
        _tracker.session_id = session_id
        _tracker.monitor.session_id = session_id
    
    if auto_record:
        _tracker.auto_record()
    
    if verbose:
        print(f"\n🏃 Agent Stamina monitoring started")
        print(f"   Session: {_tracker.session_id}")
        
        # Check if we're in OpenClaw
        if _tracker.is_openclaw():
            print(f"   OpenClaw: ✅ Detected")
            if _tracker.env.get('channel'):
                print(f"   Channel: {_tracker.env['channel']}")
        else:
            print(f"   Mode: Standalone (OpenClaw not detected)")
        
        snapshot = _tracker.monitor.current_status()
        if snapshot:
            status_emoji = {"healthy": "💚", "degraded": "💛", "critical": "🔴"}
            print(f"   Status: {status_emoji.get(snapshot.status(), '⚪')} {snapshot.status().upper()}")
            print(f"   Score: {snapshot.overall_score:.1f}/100")
        
        print()
    
    return _tracker


def stamina_snapshot(context_health: Optional[float] = None,
                     memory_freshness: Optional[float] = None,
                     error_rate: Optional[float] = None,
                     repetition_score: Optional[float] = None,
                     verbose: bool = False) -> Optional[Dict[str, Any]]:
    """Record a stamina snapshot.
    
    Auto-initializes tracker if not already started.
    
    Args:
        context_health: Context utilization (0-1), auto-estimated if None
        memory_freshness: Memory recency (0-1), defaults to 0.85
        error_rate: Error rate (0-1), defaults to 0
        repetition_score: Repetition detection (0-1), defaults to 0
        verbose: Print the recorded snapshot
        
    Returns:
        Dict with snapshot data or None if failed
    """
    global _tracker
    
    if _tracker is None:
        _tracker = monitor_me(verbose=False)
    
    _tracker.record(
        context_health=context_health,
        memory_freshness=memory_freshness,
        error_rate=error_rate,
        repetition_score=repetition_score
    )
    
    snapshot = _tracker.monitor.current_status()
    
    if verbose and snapshot:
        status_emoji = {"healthy": "💚", "degraded": "💛", "critical": "🔴"}
        print(f"{status_emoji.get(snapshot.status(), '⚪')} Stamina: {snapshot.overall_score:.1f}/100 "
              f"({snapshot.status()})")
    
    if snapshot:
        return {
            'timestamp': snapshot.timestamp.isoformat(),
            'overall_score': snapshot.overall_score,
            'status': snapshot.status(),
            'context_health': snapshot.context_health,
            'memory_freshness': snapshot.memory_freshness,
            'error_rate': snapshot.error_rate,
            'repetition_score': snapshot.repetition_score
        }
    return None


def should_checkpoint() -> bool:
    """Check if agent should checkpoint now.
    
    Returns True if stamina is degraded.
    """
    global _tracker
    
    if _tracker is None:
        return False
    
    # Check cognitive stamina only (skip gateway check to avoid hangs)
    return _tracker.monitor.should_checkpoint()


def stamina_status() -> Dict[str, Any]:
    """Get current stamina status.
    
    Returns comprehensive status including OpenClaw info.
    """
    global _tracker
    
    if _tracker is None:
        return {'error': 'Monitoring not started. Call monitor_me() first.'}
    
    return _tracker.get_status()


def my_session_time() -> float:
    """Get elapsed session time in minutes."""
    global _start_time
    
    if _start_time is None:
        return 0.0
    
    return (datetime.now() - _start_time).total_seconds() / 60


def stamina_report() -> Dict[str, Any]:
    """Generate session report."""
    global _tracker
    
    if _tracker is None:
        return {'error': 'Monitoring not started. Call monitor_me() first.'}
    
    return _tracker.monitor.generate_report()


def with_stamina_monitoring(func: Callable) -> Callable:
    """Decorator to automatically monitor a function's execution.
    
    Records snapshots before and after execution.
    
    Usage:
        @with_stamina_monitoring
        def my_long_task():
            # Your code here
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Ensure monitoring is started
        global _tracker
        if _tracker is None:
            monitor_me(verbose=True)
        
        # Record pre-execution snapshot
        stamina_snapshot(verbose=True)
        print(f"▶️  Starting: {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            
            # Record successful completion
            stamina_snapshot(verbose=True)
            print(f"✅ Completed: {func.__name__}")
            
            return result
            
        except Exception as e:
            # Record failure state
            stamina_snapshot(error_rate=1.0, verbose=True)
            print(f"❌ Failed: {func.__name__} - {e}")
            raise
    
    return wrapper


class StaminaContext:
    """Context manager for monitoring a block of code.
    
    Usage:
        with StaminaContext("processing_batch"):
            # Your code here
            process_batch()
    """
    
    def __init__(self, name: str = "task", checkpoint_interval: int = 10):
        self.name = name
        self.checkpoint_interval = checkpoint_interval
        self.start_time = None
        self.snapshots_taken = 0
    
    def __enter__(self):
        global _tracker
        if _tracker is None:
            monitor_me(verbose=True)
        
        self.start_time = time.time()
        print(f"\n🏃 Starting monitored task: {self.name}")
        stamina_snapshot(verbose=True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            print(f"✅ Task completed in {duration:.1f}s: {self.name}")
            stamina_snapshot(verbose=True)
        else:
            print(f"❌ Task failed after {duration:.1f}s: {self.name}")
            stamina_snapshot(error_rate=1.0, verbose=True)
        
        # Show final recommendation
        if should_checkpoint():
            print("⚠️  Recommendation: Consider checkpointing before next task")
        
        return False  # Don't suppress exceptions
    
    def checkpoint(self):
        """Manual checkpoint - record snapshot and check stamina."""
        self.snapshots_taken += 1
        snapshot = stamina_snapshot(verbose=False)
        
        if self.snapshots_taken % self.checkpoint_interval == 0:
            print(f"💡 Checkpoint #{self.snapshots_taken}: "
                  f"Score={snapshot['overall_score']:.1f} "
                  f"({snapshot['status']})")
        
        return snapshot


# Convenience aliases for shorter code
start_monitoring = monitor_me
snapshot = stamina_snapshot
check_stamina = stamina_status


if __name__ == "__main__":
    # Demo
    print("=" * 50)
    print("Agent Stamina - Easy Self-Monitoring Demo")
    print("=" * 50)
    
    # Method 1: Simple monitoring
    print("\n--- Method 1: Simple ---")
    tracker = monitor_me(session_id="demo-session")
    
    # Simulate some work
    for i in range(3):
        stamina_snapshot(
            context_health=0.9 - i * 0.1,
            memory_freshness=0.95 - i * 0.05,
            error_rate=0.01 * i,
            repetition_score=0.02 * i,
            verbose=True
        )
        time.sleep(0.1)
    
    # Check if we should checkpoint
    if should_checkpoint():
        print("\n⚠️  Time to checkpoint!")
    else:
        print("\n✅ Good to continue")
    
    # Get report
    report = stamina_report()
    print(f"\n📊 Session Report:")
    print(f"   Duration: {report.get('duration_minutes', 0):.1f} min")
    print(f"   Snapshots: {report.get('snapshots_count', 0)}")
    print(f"   Avg Score: {report.get('average_score', 0):.1f}")
    
    # Method 2: Context manager
    print("\n--- Method 2: Context Manager ---")
    with StaminaContext("example_task"):
        print("Doing some work...")
        time.sleep(0.1)
    
    print("\n" + "=" * 50)
    print("Demo complete!")
    print("=" * 50)
