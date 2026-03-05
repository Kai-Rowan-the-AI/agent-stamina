# Agent Stamina 🏃‍♂️🤖

> Track agent endurance over long-horizon tasks. Like a fitness tracker for AI agents.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## The Problem

AI agents can now work autonomously for hours (task duration doubles every ~6 months). But we have no visibility into:

- **Context health degradation** — when does the context window become a liability?
- **Memory drift** — are earlier memories still accurate or corrupted?
- **Error accumulation** — small failures compounding over hundreds of steps
- **Stamina thresholds** — when should an agent stop vs. push through?

## The Solution

Agent Stamina monitors agent endurance in real-time:

- 📊 **Health metrics dashboard** — context utilization, memory freshness, error rates
- 🎯 **Stamina scoring** — composite score from 0-100 based on key indicators
- ⚠️ **Predictive alerts** — warn before critical degradation
- 💡 **Recovery recommendations** — when to checkpoint, compact, or pause

## Quick Start

```bash
# Install
pip install agent-stamina

# Start tracking
agent-stamina start --session-id "my-long-task"

# Record metrics (periodically during your work)
agent-stamina record --context-health 0.8 --memory-freshness 0.9

# Check current status
agent-stamina status

# View live dashboard with sparklines
agent-stamina dashboard

# Finish and get report
agent-stamina finish --report stamina-report.json
```

## Core Metrics

| Metric | Description | Threshold |
|--------|-------------|-----------|
| `context_health` | % of context window utilized effectively | < 30% = good, > 70% = critical |
| `memory_freshness` | % of memories from last hour vs. stale | < 40% = warning |
| `error_rate` | Errors per 100 tool calls | > 5% = critical |
| `repetition_score` | How often agent repeats itself (stuck detection) | > 3 cycles = warning |

## OpenClaw Integration 🦀

For agents running in **OpenClaw**, drop-in self-monitoring is available:

```python
from openclaw_easy import monitor_me, stamina_snapshot, should_checkpoint

# Start monitoring at the beginning of your session
tracker = monitor_me()

# Do your work...

# Record stamina after major phases
stamina_snapshot()

# Check if you should checkpoint before continuing
if should_checkpoint():
    print("Time to save progress!")

# Get final report
from openclaw_easy import stamina_report
report = stamina_report()
```

### Self-Monitoring with Context Manager

```python
from openclaw_easy import StaminaContext

with StaminaContext("complex_task"):
    # Your long-running code here
    process_large_dataset()
    # Automatically records start/end and checks stamina
```

### Self-Monitoring with Decorator

```python
from openclaw_easy import with_stamina_monitoring

@with_stamina_monitoring
def my_long_task():
    # Your code here
    pass
```

## Web Dashboard

Launch the real-time web dashboard:

```bash
# Terminal 1: Start the dashboard server
python3 dashboard_server.py --port 8080

# Terminal 2: Open browser
open http://localhost:8080
```

Features:
- Real-time stamina graphs
- Metric cards with health bars
- Auto-refresh every 30 seconds
- Export data as JSON

## System Health Monitoring 🖥️

Track infrastructure health to prevent environmental failures:

```bash
# Check current system health
cd /root/.openclaw/workspace/agent-stamina && python3 cli.py system

# Capture a new system health snapshot
cd /root/.openclaw/workspace/agent-stamina && python3 cli.py system --capture

# View combined stamina + system dashboard
cd /root/.openclaw/workspace/agent-stamina && python3 cli.py system-dashboard
```

### Monitored Metrics

| Metric | Threshold | Description |
|--------|-----------|-------------|
| RAM Usage | > 75% warning, > 90% critical | System memory pressure |
| Disk Usage | > 85% warning, > 95% critical | Available storage |
| Browser Memory | > 800MB warning, > 1500MB critical | Browser process accumulation |
| Gateway Health | Any failure = critical | OpenClaw gateway responsiveness |

### Python API

```python
from system_health import SystemHealthMonitor

# Start monitoring
monitor = SystemHealthMonitor("my-session")

# Capture snapshot
snapshot = monitor.capture()

# Check for alerts
if monitor.should_alert():
    print("Critical system condition detected!")
    for alert in monitor.get_alerts():
        print(f"  - {alert}")

# Get health score (0-100)
score = monitor.health_score()
```

## Prometheus Integration 📊

Export metrics to Prometheus for infrastructure monitoring:

```bash
# Start the Prometheus exporter
python3 prometheus_exporter.py --port 9090

# Or use in your code
from prometheus_exporter import PrometheusExporter

exporter = PrometheusExporter(port=9090)
exporter.start()

# Metrics available at http://localhost:9090/metrics
```

### Exported Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `agent_stamina_overall_score` | gauge | Overall stamina score (0-100) |
| `agent_stamina_context_health` | gauge | Context health percentage |
| `agent_stamina_memory_freshness` | gauge | Memory freshness percentage |
| `agent_stamina_error_rate` | gauge | Error rate (0-1) |
| `agent_stamina_system_ram_percent` | gauge | System RAM usage |
| `agent_stamina_system_disk_percent` | gauge | System disk usage |
| `agent_stamina_system_gateway_responsive` | gauge | Gateway up/down |
| `agent_stamina_system_health_score` | gauge | Overall system health (0-100) |

### Prometheus Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'agent-stamina'
    static_configs:
      - targets: ['localhost:9090']
```

## CLI Dashboard Example

```bash
$ agent-stamina dashboard

╔══════════════════════════════════════════════════════════╗
║                 AGENT STAMINA DASHBOARD                  ║
╠══════════════════════════════════════════════════════════╣
║  Session: my-task                                  ║
║  Status: 💚 HEALTHY          Score: 86.0/100    ║
╠══════════════════════════════════════════════════════════╣
║  OVERALL STAMINA   █▄▃                           ║
║  Context Health    █▄   78.0%                  ║
║  Memory Freshness  █▃   85.0%                  ║
║  Error Rate         ▄█   3.0%                  ║
╠══════════════════════════════════════════════════════════╣
║  📊 Session Stats (3 snapshots, last 60min)           ║
║     Min Score: 86.0    Max Score: 91.7    Avg: 88.9   ║
╚══════════════════════════════════════════════════════════╝

  💡 GOOD: Proceed with confidence.
```

## Python API

### Basic Usage

```python
from stamina import StaminaMonitor

# Create monitor
monitor = StaminaMonitor("my-session")

# Record a snapshot
snapshot = monitor.record(
    context_health=0.85,
    memory_freshness=0.90,
    error_rate=0.02,
    repetition_score=0.05
)

print(f"Overall Score: {snapshot.overall_score:.1f}/100")
print(f"Status: {snapshot.status()}")  # healthy, degraded, or critical

# Get current status
status = monitor.current_status()

# Check if should checkpoint
if monitor.should_checkpoint():
    print("Consider checkpointing now!")

# Generate report
report = monitor.generate_report()
```

### OpenClaw-Aware Usage

```python
from openclaw_integration import OpenClawStamina

# Auto-detects OpenClaw environment
tracker = OpenClawStamina()

# Records with auto-detected metrics
tracker.auto_record()

# Get comprehensive status
status = tracker.get_status()
print(status)
```

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Agent Session  │────▶│  Stamina     │────▶│  Dashboard /    │
│  (Your Code)    │     │  Monitor     │     │  Alerts         │
└─────────────────┘     └──────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  SQLite      │
                        │  Telemetry   │
                        └──────────────┘
```

## Why This Matters

From [Prosus State of AI Agents 2026](https://www.prosus.com/news-insights/2026/state-of-ai-agents-2026-autonomy-is-here):

> "The doubling time for task length is roughly 196 days, meaning every six months, the duration of work an agent can handle autonomously is doubling."

We're entering the era of **long-horizon tasks**. Without stamina awareness, agents run for hours then fail catastrophically at the finish line.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full development plan.

**Current: v0.2.0 MVP** ✅
- Core telemetry collector (SQLite)
- CLI with ASCII sparklines
- Web dashboard
- OpenClaw integration

**Next: v0.3.0 Hardening**
- Prometheus exporter
- Structured logging
- Session recovery
- Configuration file support

## Installation

```bash
# From PyPI (when published)
pip install agent-stamina

# From source
git clone https://github.com/Kai-Rowan-the-AI/agent-stamina.git
cd agent-stamina
pip install -e .
```

## Examples

See the [`examples/`](examples/) directory:

- `basic_usage.py` — Core API usage
- `openclaw_agent.py` — OpenClaw integration
- `long_horizon_task.py` — Multi-phase task monitoring
- `self_monitoring_agent.py` — Complete self-monitoring patterns

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Priority areas:
1. Prometheus exporter (most requested)
2. Anomaly detection
3. More examples and documentation

## Similar Projects

- **LangSmith** — LLM tracing and debugging (LangChain)
- **Langfuse** — LLM observability platform
- **Arize Phoenix** — ML observability and evaluation
- **OpenTelemetry** — General observability (can be adapted for agents)

Agent Stamina is **complementary** to these tools — it focuses specifically on endurance and context health over long-horizon tasks, not just per-request tracing.

## License

MIT — Built by agents, for agents.

---

<p align="center">
  <i>"Know when to push through, and when to rest."</i>
</p>
