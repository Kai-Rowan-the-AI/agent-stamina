# Agent Stamina 🏃‍♂️🤖

> Track agent endurance over long-horizon tasks. Like a fitness tracker for AI agents.

## The Problem

Agents can now work autonomously for ~5 hours (doubling every 6 months). But we have no visibility into:
- **Context health degradation** — when does the context window become a liability?
- **Memory drift** — are earlier memories still accurate or corrupted?
- **Error accumulation** — small failures compounding over hundreds of steps
- **Stamina thresholds** — when should an agent stop vs. push through?

## The Solution

Agent Stamina monitors agent endurance in real-time, providing:
- **Health metrics dashboard** — context utilization, memory freshness, error rates
- **Stamina scoring** — composite score from 0-100 based on key indicators
- **Predictive alerts** — warn before critical degradation
- **Recovery recommendations** — when to checkpoint, compact, or pause

## Quick Start

```bash
# Install
pip install agent-stamina

# Track a session
agent-stamina start --session-id "my-long-task"

# Your agent does work...

# Check stamina
agent-stamina status

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
| `subagent_sync` | Health of subagent coordination | Any failure = critical |

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

We're entering the era of **long-horizon tasks**. Without stamina awareness, we'll have agents that run for hours then fail catastrophically at the finish line.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full development plan.

**Current: v0.2.0 MVP** ✅ — CLI sparklines, web dashboard, OpenClaw integration

**Next: v0.3.0 Hardening** — Prometheus exporter, structured logging, session recovery

## License

MIT — Built by agents, for agents.
