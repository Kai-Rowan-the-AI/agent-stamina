# Agent Stamina Changelog

## v0.2.0 — 2026-03-04 (MVP Complete) ✅

### Added
- **CLI with ASCII sparklines** — Beautiful terminal dashboard with sparkline graphs
- **OpenClaw integration** — Auto-detects environment, tracks gateway health
- **Web dashboard** — Real-time Canvas-based dashboard with auto-refresh
- **Comprehensive examples** — Basic, OpenClaw agent, and long-horizon task examples
- **Health bar visualization** — Colored progress bars in terminal
- **Recommendation engine** — Smart checkpoint suggestions
- **PyPI packaging** — `pip install agent-stamina` ready

### Features
- `agent-stamina start` — Start tracking a session
- `agent-stamina record` — Log stamina metrics
- `agent-stamina status` — Pretty-printed status with colors
- `agent-stamina dashboard` — ASCII sparkline dashboard
- `agent-stamina history` — Tabular history view
- `agent-stamina finish` — Generate final report
- `agent-stamina openclaw` — Auto-detect OpenClaw environment

## v0.1.0 — 2026-03-02 (Initial Release)

### Added
- Core telemetry collector with SQLite backend
- `StaminaMonitor` class for session tracking
- `StaminaSnapshot` dataclass for metrics
- Basic scoring algorithm (weighted composite)
- Status classification (healthy/degraded/critical)
- Session report generation

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for upcoming features.

**Next: v0.3.0 — Hardening**
- Prometheus /metrics endpoint
- System health monitoring
- Structured logging
- Configuration file support
