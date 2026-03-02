# Agent Stamina

Track agent endurance over long-horizon tasks. Like a fitness tracker for AI agents.

## Problem

Agents can now work autonomously for ~5 hours (doubling every 6 months). But we lack visibility into:
- Context health degradation
- Memory drift and staleness  
- Error accumulation
- When to checkpoint vs. push through

## Solution

Real-time stamina monitoring with:
- Health metrics dashboard
- Stamina scoring (0-100)
- Predictive alerts
- Recovery recommendations

## Install

```bash
pip install agent-stamina
```

## Usage

```bash
# Start session
agent-stamina start --session-id "long-task"

# Record metrics (periodically)
agent-stamina record \
  --context-health 0.8 \
  --memory-freshness 0.9 \
  --error-rate 0.02 \
  --repetition-score 0.1

# Check status
agent-stamina status

# Finish with report
agent-stamina finish --report stamina.json
```

## License

MIT
