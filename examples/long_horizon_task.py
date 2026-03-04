"""Example: Long-horizon task with periodic checks.

This example shows how to integrate stamina checks into a long-running
task with automatic recommendations.
"""

import time
from stamina import StaminaMonitor


class AgentTask:
    """Example agent that monitors its own stamina."""
    
    def __init__(self):
        self.stamina = StaminaMonitor("long-horizon-task")
        self.step_count = 0
        self.errors = 0
        self.tool_calls = 0
    
    def do_work(self):
        """Simulate doing work."""
        self.step_count += 1
        self.tool_calls += 3  # Assume 3 tool calls per step
        
        # Simulate occasional errors
        if self.step_count % 10 == 0:
            self.errors += 1
        
        time.sleep(0.1)  # Simulate work
    
    def check_stamina(self):
        """Record and check stamina."""
        # Calculate metrics based on task state
        context_health = max(0.3, 1.0 - (self.step_count * 0.01))
        memory_freshness = max(0.2, 0.95 - (self.step_count * 0.005))
        error_rate = self.errors / max(1, self.tool_calls)
        
        # Record snapshot
        snapshot = self.stamina.record(
            context_health=context_health,
            memory_freshness=memory_freshness,
            error_rate=error_rate,
            repetition_score=0.0
        )
        
        # Check and report
        print(f"\n[Step {self.step_count}] Stamina: {snapshot.overall_score:.1f}/100")
        
        if snapshot.status() == "critical":
            print("🔴 CRITICAL: Stopping for checkpoint!")
            return False
        elif snapshot.status() == "degraded":
            print("💛 DEGRADED: Consider checkpointing soon")
        
        return True
    
    def run(self, max_steps: int = 100):
        """Run the task with stamina monitoring."""
        print(f"🚀 Starting task (max {max_steps} steps)")
        print("=" * 50)
        
        for step in range(max_steps):
            self.do_work()
            
            # Check stamina every 5 steps
            if step % 5 == 0:
                if not self.check_stamina():
                    break
        
        # Final report
        print("\n" + "=" * 50)
        report = self.stamina.generate_report()
        print(f"🏁 Task complete!")
        print(f"   Steps completed: {self.step_count}")
        print(f"   Final score: {report['average_score']:.1f}/100")
        print(f"   Recommendation: {report['recommendation']}")


if __name__ == "__main__":
    task = AgentTask()
    task.run(max_steps=50)
