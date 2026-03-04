# Agent Stamina Examples 📚

This directory contains practical examples of using Agent Stamina in different scenarios.

## Examples

### [`basic_usage.py`](basic_usage.py)
Simplest possible usage - track a session, record snapshots, check status.

```bash
python examples/basic_usage.py
```

### [`openclaw_agent.py`](openclaw_agent.py)
How OpenClaw agents can self-monitor using the built-in integration.

```bash
python examples/openclaw_agent.py
```

### [`long_horizon_task.py`](long_horizon_task.py)
Long-running task with periodic stamina checks and automatic checkpoint recommendations.

```bash
python examples/long_horizon_task.py
```

## Quick CLI Examples

```bash
# Start a session
agent-stamina start --session-id "my-task"

# Record metrics (these would come from your agent)
agent-stamina record \
  --context-health 0.8 \
  --memory-freshness 0.9 \
  --error-rate 0.02 \
  --repetition-score 0.1

# Check status with pretty colors
agent-stamina status

# Show live dashboard with sparklines
agent-stamina dashboard

# View history table
agent-stamina history --minutes 60 --limit 20

# Auto-detect OpenClaw environment
agent-stamina openclaw

# Finish and generate report
agent-stamina finish --report stamina-report.json
```

## Programmatic Usage

```python
from stamina import StaminaMonitor
from openclaw_integration import OpenClawStamina

# Basic usage
monitor = StaminaMonitor("my-session")
monitor.record(context_health=0.85, memory_freshness=0.9, 
               error_rate=0.02, repetition_score=0.0)

# OpenClaw auto-integration
tracker = OpenClawStamina()
tracker.auto_record()  # Auto-detects environment
if tracker.should_checkpoint():
    print("Time to checkpoint!")
```
