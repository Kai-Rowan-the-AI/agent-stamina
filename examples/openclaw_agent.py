"""Example: OpenClaw agent self-monitoring.

This example shows how an OpenClaw agent can monitor its own stamina
using the built-in integration.
"""

from openclaw_integration import OpenClawStamina, quick_check

# Method 1: One-liner check
print("=== Quick Check ===")
tracker = quick_check()

# Method 2: Full control
print("\n=== Detailed Tracking ===")
tracker = OpenClawStamina()

# Auto-detect and record based on environment
tracker.auto_record()

# Check comprehensive status
status = tracker.get_status()
print(f"OpenClaw detected: {status['openclaw']['detected']}")
print(f"Gateway responsive: {status['gateway_health']['responsive']}")

# Manual recording with custom metrics
tracker.record(
    context_health=0.75,
    memory_freshness=0.88,
    error_rate=0.03,
    repetition_score=0.10
)

# Check if we should checkpoint
if tracker.should_checkpoint():
    print("\n⚠️  Time to checkpoint! Gateway or stamina is degraded.")
else:
    print("\n✅ Good to continue working.")

# Get history
history = tracker.monitor.get_history(minutes=60)
print(f"\nRecorded {len(history)} snapshots in the last hour")
