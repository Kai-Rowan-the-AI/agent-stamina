#!/usr/bin/env python3
"""Agent Stamina CLI - Command line interface for agent endurance monitoring."""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Optional

from stamina import StaminaMonitor, StaminaSnapshot
from system_health import SystemHealthMonitor


def sparkline(values: list[float], width: int = 20) -> str:
    """Generate ASCII sparkline from values."""
    if not values:
        return "─" * width
    
    blocks = " ▁▂▃▄▅▆▇█"
    min_val, max_val = min(values), max(values)
    
    if max_val == min_val:
        return "─" * width
    
    # Scale to width
    if len(values) <= width:
        indices = list(range(len(values)))
    else:
        # Sample evenly
        step = len(values) / width
        indices = [int(i * step) for i in range(width)]
    
    result = ""
    for i in indices:
        val = values[i]
        # Normalize to 0-8 range
        normalized = (val - min_val) / (max_val - min_val)
        block_idx = int(normalized * 8)
        result += blocks[block_idx]
    
    return result


def health_bar(value: float, width: int = 20) -> str:
    """Generate colored health bar."""
    filled = int(value / 100 * width)
    empty = width - filled
    
    if value >= 70:
        color = "\033[92m"  # Green
    elif value >= 40:
        color = "\033[93m"  # Yellow
    else:
        color = "\033[91m"  # Red
    
    reset = "\033[0m"
    return f"{color}{'█' * filled}{'░' * empty}{reset} {value:.1f}%"


def cmd_start(args):
    """Start a new stamina tracking session."""
    session_id = args.session_id or f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    monitor = StaminaMonitor(session_id, db_path=args.db)
    
    # Store active session
    os.makedirs(os.path.expanduser("~/.agent-stamina"), exist_ok=True)
    with open(os.path.expanduser("~/.agent-stamina/active-session"), "w") as f:
        f.write(f"{session_id}\n{args.db}")
    
    print(f"\n🏃 Started stamina tracking: {session_id}")
    print(f"   Database: {args.db}")
    print(f"\n   Use 'agent-stamina record' to log metrics")
    print(f"   Use 'agent-stamina status' to check current stamina")
    print(f"   Use 'agent-stamina dashboard' for live monitoring\n")


def cmd_record(args):
    """Record a stamina snapshot."""
    session_id, db_path = _get_active_session()
    
    monitor = StaminaMonitor(session_id, db_path=db_path)
    
    snapshot = monitor.record(
        context_health=args.context_health,
        memory_freshness=args.memory_freshness,
        error_rate=args.error_rate,
        repetition_score=args.repetition_score
    )
    
    print(f"\n✅ Recorded snapshot: {snapshot.status().upper()}")
    print(f"   Overall Score: {snapshot.overall_score:.1f}/100")
    print(f"   Context Health: {snapshot.context_health*100:.1f}%")
    print(f"   Memory Freshness: {snapshot.memory_freshness*100:.1f}%")
    print(f"   Error Rate: {snapshot.error_rate*100:.1f}%")


def cmd_status(args):
    """Show current stamina status."""
    session_id, db_path = _get_active_session()
    
    monitor = StaminaMonitor(session_id, db_path=db_path)
    snapshot = monitor.current_status()
    
    if not snapshot:
        print("\n⚠️  No stamina data recorded yet.")
        print("   Run 'agent-stamina record' to log your first snapshot.\n")
        return
    
    # Status emoji
    status_emoji = {
        "healthy": "💚",
        "degraded": "💛", 
        "critical": "🔴"
    }.get(snapshot.status(), "⚪")
    
    print(f"\n{status_emoji}  Stamina Status: {snapshot.status().upper()}")
    print(f"   Session: {session_id}")
    print(f"   Timestamp: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"   Overall Score: {health_bar(snapshot.overall_score)}")
    print(f"   Context Health: {health_bar(snapshot.context_health * 100)}")
    print(f"   Memory Freshness: {health_bar(snapshot.memory_freshness * 100)}")
    print(f"   Error Rate: {health_bar((1 - snapshot.error_rate) * 100)}")
    print(f"   Repetition Score: {health_bar((1 - snapshot.repetition_score) * 100)}")
    print()
    
    # Recommendation
    rec = monitor._get_recommendation(snapshot)
    print(f"   💡 {rec}\n")


def cmd_dashboard(args):
    """Show live dashboard with sparklines."""
    session_id, db_path = _get_active_session()
    
    monitor = StaminaMonitor(session_id, db_path=db_path)
    history = monitor.get_history(minutes=args.minutes)
    
    if not history:
        print("\n⚠️  No stamina data available.")
        print(f"   Run 'agent-stamina record' to start collecting data.\n")
        return
    
    # Clear screen
    os.system('clear' if os.name != 'nt' else 'cls')
    
    print("╔" + "═" * 58 + "╗")
    print("║" + " AGENT STAMINA DASHBOARD ".center(58) + "║")
    print("╠" + "═" * 58 + "╣")
    
    # Current status
    current = history[-1]
    status_emoji = {"healthy": "💚", "degraded": "💛", "critical": "🔴"}.get(current.status(), "⚪")
    
    print(f"║  Session: {session_id[:40]:<40} ║")
    print(f"║  Status: {status_emoji} {current.status().upper():<16} Score: {current.overall_score:.1f}/100    ║")
    print("╠" + "═" * 58 + "╣")
    
    # Sparklines
    scores = [h.overall_score for h in history]
    context = [h.context_health * 100 for h in history]
    memory = [h.memory_freshness * 100 for h in history]
    errors = [h.error_rate * 100 for h in history]
    
    print(f"║  OVERALL STAMINA   {sparkline(scores, 30)}           ║")
    print(f"║  Context Health    {sparkline(context, 30)} {context[-1]:5.1f}%  ║")
    print(f"║  Memory Freshness  {sparkline(memory, 30)} {memory[-1]:5.1f}%  ║")
    print(f"║  Error Rate        {sparkline(errors, 30)} {errors[-1]:5.1f}%  ║")
    print("╠" + "═" * 58 + "╣")
    
    # Stats
    print(f"║  📊 Session Stats ({len(history)} snapshots, last {args.minutes}min)           ║")
    print(f"║     Min Score: {min(scores):.1f}    Max Score: {max(scores):.1f}    Avg: {sum(scores)/len(scores):.1f}   ║")
    print("╚" + "═" * 58 + "╝")
    
    # Recommendation
    rec = monitor._get_recommendation(current)
    print(f"\n  💡 {rec}\n")


def cmd_history(args):
    """Show historical snapshots."""
    session_id, db_path = _get_active_session()
    
    monitor = StaminaMonitor(session_id, db_path=db_path)
    history = monitor.get_history(minutes=args.minutes)
    
    if not history:
        print("\n⚠️  No history available.\n")
        return
    
    print(f"\n📈 Stamina History (last {args.minutes} minutes)\n")
    print(f"{'Time':<12} {'Status':<10} {'Score':>8} {'Context':>10} {'Memory':>10} {'Errors':>8}")
    print("-" * 66)
    
    for snap in history[-args.limit:]:
        time_str = snap.timestamp.strftime("%H:%M:%S")
        status_icon = {"healthy": "✓", "degraded": "~", "critical": "!"}.get(snap.status(), "?")
        print(f"{time_str:<12} {status_icon} {snap.status():<8} {snap.overall_score:>7.1f}% "
              f"{snap.context_health*100:>9.1f}% {snap.memory_freshness*100:>9.1f}% {snap.error_rate*100:>7.1f}%")
    print()


def cmd_finish(args):
    """Finish session and generate report."""
    session_id, db_path = _get_active_session()
    
    monitor = StaminaMonitor(session_id, db_path=db_path)
    report = monitor.generate_report()
    
    print(f"\n🏁 Session Complete: {session_id}\n")
    print(f"   Duration: {report['duration_minutes']:.1f} minutes")
    print(f"   Snapshots: {report['snapshots_count']}")
    print(f"   Average Score: {report['average_score']:.1f}/100")
    print(f"   Min/Max Score: {report['min_score']:.1f} / {report['max_score']:.1f}")
    print(f"   Final Status: {report['current_status'].upper()}")
    print(f"\n   {report['recommendation']}\n")
    
    if args.report:
        with open(args.report, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📄 Report saved to: {args.report}\n")
    
    # Clear active session
    active_file = os.path.expanduser("~/.agent-stamina/active-session")
    if os.path.exists(active_file):
        os.remove(active_file)


def cmd_system_health(args):
    """Show system health status."""
    session_id, db_path = _get_active_session()
    
    monitor = SystemHealthMonitor(session_id, db_path=db_path)
    
    if args.capture:
        snapshot = monitor.capture()
        print(f"\n📸 Captured system health snapshot")
    else:
        snapshot = monitor.current_status()
    
    if not snapshot:
        print("\n⚠️  No system health data recorded yet.")
        print("   Run 'agent-stamina system --capture' to collect data.\n")
        return
    
    # Status emoji
    status_emoji = {
        "healthy": "💚",
        "warning": "💛", 
        "critical": "🔴"
    }.get(snapshot.status, "⚪")
    
    print(f"\n{status_emoji}  System Health: {snapshot.status.upper()}")
    print(f"   Session: {session_id}")
    print(f"   Timestamp: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # RAM bar
    ram_color = "\033[92m" if snapshot.ram_percent < 60 else "\033[93m" if snapshot.ram_percent < 75 else "\033[91m"
    ram_filled = int(snapshot.ram_percent / 100 * 20)
    ram_bar = f"{ram_color}{'█' * ram_filled}{'░' * (20 - ram_filled)}\033[0m"
    print(f"   💾 RAM:        {ram_bar} {snapshot.ram_percent:.1f}%")
    print(f"               ({snapshot.ram_used_mb:.0f} / {snapshot.ram_total_mb:.0f} MB)")
    
    # Disk bar
    disk_color = "\033[92m" if snapshot.disk_percent < 70 else "\033[93m" if snapshot.disk_percent < 85 else "\033[91m"
    disk_filled = int(snapshot.disk_percent / 100 * 20)
    disk_bar = f"{disk_color}{'█' * disk_filled}{'░' * (20 - disk_filled)}\033[0m"
    print(f"   💿 Disk:       {disk_bar} {snapshot.disk_percent:.1f}%")
    print(f"               ({snapshot.disk_free_gb:.1f} GB free)")
    
    # Browser
    if snapshot.browser_memory_mb:
        browser_color = "\033[92m" if snapshot.browser_memory_mb < 500 else "\033[93m" if snapshot.browser_memory_mb < 800 else "\033[91m"
        print(f"   🌐 Browser:    {browser_color}{snapshot.browser_memory_mb:.0f} MB\033[0m ({snapshot.browser_processes} processes)")
    else:
        print(f"   🌐 Browser:    Not detected")
    
    # Gateway
    if snapshot.gateway_responsive:
        gw_emoji = "✅"
        gw_status = f"Responsive ({snapshot.gateway_latency_ms:.1f}ms)"
    else:
        gw_emoji = "🔴"
        gw_status = "Unresponsive"
    print(f"   🦀 Gateway:    {gw_emoji} {gw_status}")
    
    # Health score
    health_score = monitor.health_score()
    print(f"\n   📊 Health Score: {health_bar(health_score)}")
    
    # Alerts
    if snapshot.alerts:
        print(f"\n   ⚠️  Alerts:")
        for alert in snapshot.alerts:
            alert_emoji = "🔴" if "CRITICAL" in alert else "💛"
            print(f"      {alert_emoji} {alert}")
    else:
        print(f"\n   ✅ No alerts")
    
    print()


def cmd_system_dashboard(args):
    """Show combined stamina and system health dashboard."""
    session_id, db_path = _get_active_session()
    
    stamina_monitor = StaminaMonitor(session_id, db_path=db_path)
    system_monitor = SystemHealthMonitor(session_id, db_path=db_path)
    
    stamina_history = stamina_monitor.get_history(minutes=args.minutes)
    system_history = system_monitor.get_history(minutes=args.minutes)
    
    # Clear screen
    os.system('clear' if os.name != 'nt' else 'cls')
    
    print("╔" + "═" * 58 + "╗")
    print("║" + " AGENT STAMINA + SYSTEM HEALTH ".center(58) + "║")
    print("╠" + "═" * 58 + "╣")
    
    # Stamina section
    if stamina_history:
        current = stamina_history[-1]
        status_emoji = {"healthy": "💚", "degraded": "💛", "critical": "🔴"}.get(current.status(), "⚪")
        print(f"║  🏃 Stamina: {status_emoji} {current.status().upper():<12} Score: {current.overall_score:.1f}/100    ║")
        
        scores = [h.overall_score for h in stamina_history]
        print(f"║     Overall: {sparkline(scores, 30)} {scores[-1]:5.1f}%       ║")
    else:
        print(f"║  🏃 Stamina: No data recorded                           ║")
    
    print("║" + " " * 58 + "║")
    
    # System health section
    if system_history:
        current = system_history[-1]
        status_emoji = {"healthy": "💚", "warning": "💛", "critical": "🔴"}.get(current.status, "⚪")
        print(f"║  🖥️  System:  {status_emoji} {current.status.upper():<12} Score: {system_monitor.health_score():.1f}/100    ║")
        
        ram_values = [h.ram_percent for h in system_history]
        print(f"║     RAM:     {sparkline(ram_values, 30)} {ram_values[-1]:5.1f}%       ║")
        
        if current.browser_memory_mb:
            print(f"║     Browser: {current.browser_memory_mb:.0f} MB ({current.browser_processes} procs)           ║")
        
        gw_status = "✅ UP" if current.gateway_responsive else "🔴 DOWN"
        print(f"║     Gateway: {gw_status}                                    ║")
    else:
        print(f"║  🖥️  System:  No data recorded                           ║")
    
    print("╚" + "═" * 58 + "╝")
    
    # Alerts
    if system_history and system_history[-1].alerts:
        print("\n  ⚠️  System Alerts:")
        for alert in system_history[-1].alerts[:3]:
            print(f"     {alert}")
    
    if stamina_history:
        rec = stamina_monitor._get_recommendation(stamina_history[-1])
        print(f"\n  💡 {rec}")
    print()


def cmd_openclaw(args):
    # Check for OpenClaw environment variables
    env_vars = {
        'OPENCLAW_SESSION_KEY': os.environ.get('OPENCLAW_SESSION_KEY'),
        'OPENCLAW_AGENT_ID': os.environ.get('OPENCLAW_AGENT_ID'),
        'OPENCLAW_CONTEXT_SIZE': os.environ.get('OPENCLAW_CONTEXT_SIZE'),
        'OPENCLAW_START_TIME': os.environ.get('OPENCLAW_START_TIME'),
    }
    
    detected = {k: v for k, v in env_vars.items() if v}
    
    if not detected:
        print("\n❌ No OpenClaw environment detected.\n")
        print("   Make sure you're running within an OpenClaw session.")
        print("   Expected env vars: OPENCLAW_SESSION_KEY, OPENCLAW_AGENT_ID\n")
        return
    
    print("\n✅ OpenClaw Environment Detected\n")
    for var, val in detected.items():
        display_val = val[:50] + "..." if len(val) > 50 else val
        print(f"   {var}: {display_val}")
    
    # Auto-configure session
    session_id = env_vars['OPENCLAW_SESSION_KEY'] or f"openclaw-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Try to estimate context health from environment
    context_size = env_vars.get('OPENCLAW_CONTEXT_SIZE')
    if context_size:
        try:
            ctx = int(context_size)
            # Assume healthy if under 50% of some assumed max
            context_health = max(0.0, 1.0 - (ctx / 200000))
            print(f"\n   Estimated Context Health: {context_health*100:.1f}%")
        except:
            context_health = 0.8
    else:
        context_health = 0.8
    
    monitor = StaminaMonitor(session_id)
    
    # Store as active
    os.makedirs(os.path.expanduser("~/.agent-stamina"), exist_ok=True)
    with open(os.path.expanduser("~/.agent-stamina/active-session"), "w") as f:
        f.write(f"{session_id}\n.agent_stamina.db")
    
    print(f"\n   Auto-configured session: {session_id}")
    print(f"   Use 'agent-stamina record' to log metrics\n")


def _get_active_session():
    """Get currently active session from file."""
    active_file = os.path.expanduser("~/.agent-stamina/active-session")
    
    if os.path.exists(active_file):
        with open(active_file) as f:
            lines = f.read().strip().split('\n')
            session_id = lines[0]
            db_path = lines[1] if len(lines) > 1 else ".agent_stamina.db"
            return session_id, db_path
    
    # Fallback: create default
    return f"default-{datetime.now().strftime('%Y%m%d')}", ".agent_stamina.db"


def main():
    parser = argparse.ArgumentParser(
        description="Agent Stamina - Monitor agent endurance over long-horizon tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agent-stamina start --session-id "my-task"
  agent-stamina record --context-health 0.8 --memory-freshness 0.9
  agent-stamina status
  agent-stamina dashboard
  agent-stamina system --capture          # Capture system health snapshot
  agent-stamina system-dashboard          # Combined stamina + system view
  agent-stamina finish --report report.json
        """
    )
    
    parser.add_argument("--db", default=".agent_stamina.db", help="Database path")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # start
    start_parser = subparsers.add_parser("start", help="Start a new session")
    start_parser.add_argument("--session-id", help="Session identifier")
    
    # record
    record_parser = subparsers.add_parser("record", help="Record a stamina snapshot")
    record_parser.add_argument("--context-health", type=float, default=0.8, help="Context health (0-1)")
    record_parser.add_argument("--memory-freshness", type=float, default=0.9, help="Memory freshness (0-1)")
    record_parser.add_argument("--error-rate", type=float, default=0.0, help="Error rate (0-1)")
    record_parser.add_argument("--repetition-score", type=float, default=0.0, help="Repetition score (0-1)")
    
    # status
    subparsers.add_parser("status", help="Show current stamina status")
    
    # dashboard
    dashboard_parser = subparsers.add_parser("dashboard", help="Show live dashboard")
    dashboard_parser.add_argument("--minutes", type=int, default=60, help="History window in minutes")
    
    # history
    history_parser = subparsers.add_parser("history", help="Show historical data")
    history_parser.add_argument("--minutes", type=int, default=60, help="History window")
    history_parser.add_argument("--limit", type=int, default=20, help="Max entries to show")
    
    # finish
    finish_parser = subparsers.add_parser("finish", help="Finish session and generate report")
    finish_parser.add_argument("--report", help="Save report to file")
    
    # openclaw
    subparsers.add_parser("openclaw", help="Auto-detect OpenClaw environment")
    
    # system health
    system_parser = subparsers.add_parser("system", help="Show system health status")
    system_parser.add_argument("--capture", action="store_true", help="Capture new snapshot")
    
    # system dashboard
    system_dash_parser = subparsers.add_parser("system-dashboard", help="Show combined stamina + system dashboard")
    system_dash_parser.add_argument("--minutes", type=int, default=60, help="History window in minutes")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        "start": cmd_start,
        "record": cmd_record,
        "status": cmd_status,
        "dashboard": cmd_dashboard,
        "history": cmd_history,
        "finish": cmd_finish,
        "openclaw": cmd_openclaw,
        "system": cmd_system_health,
        "system-dashboard": cmd_system_dashboard,
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
