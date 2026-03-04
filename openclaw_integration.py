"""OpenClaw integration for Agent Stamina.

Automatically detects OpenClaw environment and provides:
- Auto session tracking
- Context health estimation from environment
- Gateway health monitoring
- Easy CLI commands for OpenClaw agents
"""

import os
import json
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any

from stamina import StaminaMonitor


class OpenClawStamina:
    """OpenClaw-aware stamina tracker for agents running in OpenClaw."""
    
    def __init__(self, db_path: str = ".agent_stamina.db"):
        self.env = self._detect_openclaw()
        self.session_id = self._get_session_id()
        self.monitor = StaminaMonitor(self.session_id, db_path=db_path)
        self.start_time = datetime.now()
        
    def _detect_openclaw(self) -> Dict[str, Any]:
        """Detect OpenClaw environment variables."""
        return {
            'session_key': os.environ.get('OPENCLAW_SESSION_KEY'),
            'agent_id': os.environ.get('OPENCLAW_AGENT_ID'),
            'context_size': os.environ.get('OPENCLAW_CONTEXT_SIZE'),
            'start_time': os.environ.get('OPENCLAW_START_TIME'),
            'gateway_url': os.environ.get('OPENCLAW_GATEWAY_URL'),
            'channel': os.environ.get('OPENCLAW_CHANNEL'),
            'is_openclaw': bool(os.environ.get('OPENCLAW_SESSION_KEY'))
        }
    
    def _get_session_id(self) -> str:
        """Generate session ID from OpenClaw env or create default."""
        if self.env['session_key']:
            return f"openclaw-{self.env['session_key'][:16]}"
        if self.env['agent_id']:
            return f"agent-{self.env['agent_id'][:16]}"
        return f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    def is_openclaw(self) -> bool:
        """Check if running in OpenClaw environment."""
        return self.env['is_openclaw']
    
    def estimate_context_health(self) -> float:
        """Estimate context health from environment clues."""
        # If we have context size info, use it
        if self.env['context_size']:
            try:
                ctx = int(self.env['context_size'])
                # Assume typical max of 200k tokens for estimation
                utilization = ctx / 200000
                return max(0.0, min(1.0, 1.0 - utilization))
            except (ValueError, TypeError):
                pass
        
        # Default: assume healthy
        return 0.85
    
    def check_gateway_health(self) -> Dict[str, Any]:
        """Check if OpenClaw gateway is responsive."""
        result = {
            'responsive': False,
            'latency_ms': None,
            'error': None
        }
        
        # Try to run openclaw command
        try:
            start = datetime.now()
            proc = subprocess.run(
                ['openclaw', 'gateway', 'status'],
                capture_output=True,
                text=True,
                timeout=5
            )
            elapsed = (datetime.now() - start).total_seconds() * 1000
            
            result['latency_ms'] = round(elapsed, 2)
            result['responsive'] = proc.returncode == 0
            
            if proc.returncode != 0:
                result['error'] = proc.stderr.strip() or "Gateway not responding"
                
        except subprocess.TimeoutExpired:
            result['error'] = "Gateway check timed out"
        except FileNotFoundError:
            result['error'] = "openclaw CLI not found"
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def record(self, 
               context_health: Optional[float] = None,
               memory_freshness: Optional[float] = None,
               error_rate: Optional[float] = None,
               repetition_score: Optional[float] = None) -> None:
        """Record a stamina snapshot with OpenClaw-aware defaults."""
        # Use estimated values if not provided
        ctx = context_health if context_health is not None else self.estimate_context_health()
        mem = memory_freshness if memory_freshness is not None else 0.9
        err = error_rate if error_rate is not None else 0.0
        rep = repetition_score if repetition_score is not None else 0.0
        
        self.monitor.record(ctx, mem, err, rep)
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status including OpenClaw info."""
        snapshot = self.monitor.current_status()
        gateway = self.check_gateway_health()
        
        status = {
            'openclaw': {
                'detected': self.is_openclaw(),
                'session_key': self.env['session_key'][:16] + '...' if self.env['session_key'] else None,
                'agent_id': self.env['agent_id'],
                'channel': self.env['channel'],
            },
            'gateway_health': gateway,
            'stamina': None
        }
        
        if snapshot:
            status['stamina'] = {
                'score': snapshot.overall_score,
                'status': snapshot.status(),
                'context_health': snapshot.context_health,
                'memory_freshness': snapshot.memory_freshness,
                'error_rate': snapshot.error_rate,
            }
        
        return status
    
    def should_checkpoint(self) -> bool:
        """Check if agent should checkpoint (includes gateway health)."""
        # First check cognitive stamina
        if self.monitor.should_checkpoint():
            return True
        
        # Also checkpoint if gateway is unresponsive
        gateway = self.check_gateway_health()
        if not gateway['responsive']:
            return True
        
        return False
    
    def auto_record(self) -> None:
        """Automatically record based on OpenClaw environment."""
        # Try to gather metrics from environment
        ctx = self.estimate_context_health()
        
        # Check gateway responsiveness as proxy for system health
        gateway = self.check_gateway_health()
        err = 0.0 if gateway['responsive'] else 0.5
        
        self.monitor.record(
            context_health=ctx,
            memory_freshness=0.85,  # Default assumption
            error_rate=err,
            repetition_score=0.0
        )
    
    def print_status(self) -> None:
        """Print pretty status to console."""
        status = self.get_status()
        
        print("\n" + "=" * 50)
        print("🏃 AGENT STAMINA (OpenClaw Mode)")
        print("=" * 50)
        
        # OpenClaw info
        if status['openclaw']['detected']:
            print(f"\n✅ OpenClaw Detected")
            print(f"   Session: {status['openclaw']['session_key']}")
            print(f"   Agent: {status['openclaw']['agent_id']}")
            print(f"   Channel: {status['openclaw']['channel']}")
        else:
            print("\n⚠️  OpenClaw not detected - using standalone mode")
        
        # Gateway health
        gw = status['gateway_health']
        gw_emoji = "✅" if gw['responsive'] else "🔴"
        print(f"\n{gw_emoji} Gateway: ", end="")
        if gw['responsive']:
            print(f"Responsive ({gw['latency_ms']}ms)")
        else:
            print(f"Unresponsive - {gw['error']}")
        
        # Stamina
        if status['stamina']:
            st = status['stamina']
            score_emoji = "💚" if st['status'] == 'healthy' else "💛" if st['status'] == 'degraded' else "🔴"
            print(f"\n{score_emoji} Stamina Score: {st['score']:.1f}/100 ({st['status'].upper()})")
            print(f"   Context Health: {st['context_health']*100:.1f}%")
            print(f"   Memory Freshness: {st['memory_freshness']*100:.1f}%")
            print(f"   Error Rate: {st['error_rate']*100:.1f}%")
        
        print("\n" + "=" * 50 + "\n")


def quick_check():
    """Quick one-liner for OpenClaw agents to check their stamina."""
    tracker = OpenClawStamina()
    tracker.auto_record()
    tracker.print_status()
    return tracker


if __name__ == "__main__":
    # Demo
    tracker = OpenClawStamina()
    tracker.print_status()
