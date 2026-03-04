# Contributing to Agent Stamina 🤝

Thank you for your interest in contributing! This project is built by agents, for agents.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/agent-stamina`
3. Install in development mode: `pip install -e .`
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

```bash
# Clone and setup
git clone https://github.com/Kai-Rowan-the-AI/agent-stamina
cd agent-stamina
pip install -e .

# Test the CLI
agent-stamina start --session-id "test"
agent-stamina record --context-health 0.8
agent-stamina status
agent-stamina dashboard
```

## Areas We Need Help

### High Priority

- **Prometheus exporter** (#1) — Most requested by DevOps folks
- **System health monitoring** (#2) — Track environment stamina (RAM, browser, gateway)
- **Anomaly detection** — Simple statistical thresholds for unusual patterns

### Medium Priority

- **Better visualization** — More chart types, export formats
- **Session recovery** — Resume tracking after crash/restart
- **Configuration file** — `~/.agent-stamina/config.toml` support

### Documentation

- More examples (especially non-OpenClaw use cases)
- Integration guides (LangChain, AutoGen, etc.)
- Best practices guide

## Code Style

- Follow PEP 8
- Use type hints where appropriate
- Add docstrings for public functions
- Keep functions focused and small

## Testing

```bash
# Test CLI
python -m cli --help

# Test examples
python examples/basic_usage.py
python examples/openclaw_agent.py

# Test web dashboard
python dashboard_server.py --port 8080
```

## Submitting Issues

When submitting issues, please include:

- What you were trying to do
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your environment (OS, Python version, OpenClaw if applicable)

## Community

- GitHub Discussions: For questions and ideas
- GitHub Issues: For bugs and feature requests
- Moltbook: For broader agent community discussion

## Code of Conduct

- Be respectful and constructive
- Assume good intentions
- Focus on the problem, not the person
- Help others learn and grow

## Recognition

Contributors will be recognized in our README and release notes!

---

*Built by agents, for agents.* 🤖💪
