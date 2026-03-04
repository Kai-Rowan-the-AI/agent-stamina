"""Example: Basic stamina tracking.

This example shows the simplest way to use Agent Stamina
to track an agent session.
"""

from stamina import StaminaMonitor

# Start tracking
monitor = StaminaMonitor("my-task-session")

# Your agent does work...
# Periodically record stamina metrics

# After some work
monitor.record(
    context_health=0.85,    # 85% of context window used effectively
    memory_freshness=0.92,  # 92% of memories are recent
    error_rate=0.02,        # 2% error rate
    repetition_score=0.05   # Low repetition
)

# Later, after more work...
monitor.record(
    context_health=0.72,
    memory_freshness=0.78,
    error_rate=0.05,
    repetition_score=0.15
)

# Check current status
status = monitor.current_status()
print(f"Current stamina: {status.overall_score:.1f}/100 ({status.status()})")

# Get recommendation
if monitor.should_checkpoint():
    print("⚠️  Consider checkpointing now!")

# Finish and get report
report = monitor.generate_report()
print(f"\nSession complete!")
print(f"Duration: {report['duration_minutes']:.1f} minutes")
print(f"Average score: {report['average_score']:.1f}/100")
