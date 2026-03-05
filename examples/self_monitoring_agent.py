"""Example: Self-monitoring OpenClaw Agent

This example shows how an OpenClaw agent can monitor its own stamina
throughout a long-horizon task using the easy monitoring API.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import the easy monitoring API
from openclaw_easy import (
    monitor_me,           # Start monitoring
    stamina_snapshot,     # Record a snapshot
    should_checkpoint,    # Check if it's time to checkpoint
    stamina_status,       # Get current status
    stamina_report,       # Generate final report
    StaminaContext,       # Context manager for tasks
    with_stamina_monitoring  # Decorator for functions
)


def example_basic_monitoring():
    """Example 1: Basic monitoring throughout your work."""
    
    # Start monitoring at the beginning of your session
    print("=" * 60)
    print("Example 1: Basic Monitoring")
    print("=" * 60)
    
    tracker = monitor_me(session_id="my-task-session")
    
    # Simulate doing some work...
    print("\n📋 Phase 1: Initial analysis")
    # ... your code here ...
    stamina_snapshot(context_health=0.9, memory_freshness=0.95, verbose=True)
    
    print("\n📋 Phase 2: Processing data")
    # ... more work ...
    stamina_snapshot(context_health=0.85, memory_freshness=0.88, verbose=True)
    
    print("\n📋 Phase 3: Complex reasoning")
    # ... intense work that might degrade context ...
    stamina_snapshot(context_health=0.75, memory_freshness=0.80, verbose=True)
    
    # Check if we should checkpoint before continuing
    if should_checkpoint():
        print("\n⚠️  CHECKPOINT RECOMMENDED!")
        print("   Consider saving progress before continuing.")
    
    # Get final report
    report = stamina_report()
    print(f"\n📊 Final Report:")
    print(f"   Session: {report['session_id']}")
    print(f"   Duration: {report['duration_minutes']:.1f} minutes")
    print(f"   Average Score: {report['average_score']:.1f}/100")
    print(f"   Final Status: {report['current_status']}")


def example_context_manager():
    """Example 2: Using context manager for complex tasks."""
    
    print("\n" + "=" * 60)
    print("Example 2: Context Manager")
    print("=" * 60)
    
    # Monitor a complex task with automatic checkpointing
    with StaminaContext("data_processing_pipeline", checkpoint_interval=3):
        
        print("\nStep 1: Loading data...")
        # ... load data ...
        
        print("Step 2: Transforming...")
        # ... transform ...
        
        print("Step 3: Analyzing...")
        # ... analyze ...
        
        print("Step 4: Generating output...")
        # ... generate ...


def example_decorator():
    """Example 3: Using decorator for monitored functions."""
    
    print("\n" + "=" * 60)
    print("Example 3: Function Decorator")
    print("=" * 60)
    
    @with_stamina_monitoring
    def analyze_large_dataset(dataset_path: str):
        """A function that analyzes a large dataset."""
        print(f"Analyzing {dataset_path}...")
        # ... analysis code ...
        return {"records_processed": 10000}
    
    @with_stamina_monitoring
    def generate_report(results: dict):
        """Generate a report from results."""
        print("Generating report...")
        # ... report generation ...
        return "report.pdf"
    
    # Run monitored functions
    results = analyze_large_dataset("data/large_dataset.csv")
    report_path = generate_report(results)
    
    print(f"\n✅ Generated: {report_path}")


def example_periodic_checkpoints():
    """Example 4: Periodic checkpoints in long-running tasks."""
    
    print("\n" + "=" * 60)
    print("Example 4: Periodic Checkpoints")
    print("=" * 60)
    
    # Start monitoring
    monitor_me(session_id="long-task")
    
    # Simulate a long task with many iterations
    total_items = 10
    checkpoint_every = 3
    
    for i in range(total_items):
        print(f"\n📦 Processing item {i+1}/{total_items}...")
        # ... process item ...
        
        # Record snapshot every few iterations
        if (i + 1) % checkpoint_every == 0:
            snapshot = stamina_snapshot(verbose=True)
            
            if should_checkpoint():
                print(f"   ⚠️  Degraded at item {i+1}! Consider checkpointing.")
            else:
                print(f"   ✅ Healthy at item {i+1}, continuing...")
    
    # Final report
    report = stamina_report()
    print(f"\n📊 Task completed!")
    print(f"   Total snapshots: {report['snapshots_count']}")
    print(f"   Min score: {report['min_score']:.1f}")
    print(f"   Max score: {report['max_score']:.1f}")


def example_error_handling():
    """Example 5: Monitoring with error handling."""
    
    print("\n" + "=" * 60)
    print("Example 5: Error Handling")
    print("=" * 60)
    
    monitor_me(session_id="error-demo")
    
    try:
        with StaminaContext("risky_operation"):
            print("Starting risky operation...")
            stamina_snapshot(verbose=True)
            
            # Simulate an error
            raise ValueError("Something went wrong!")
            
    except ValueError as e:
        print(f"\n📝 Caught error: {e}")
        
        # Check stamina even after errors
        status = stamina_status()
        if status.get('stamina'):
            print(f"   Stamina after error: {status['stamina']['score']:.1f}/100")
        
        # Decide whether to retry or abort
        if should_checkpoint():
            print("   ⚠️  Stamina critical after error. Abort recommended.")
        else:
            print("   ✅ Still healthy. Could retry with fresh context.")


if __name__ == "__main__":
    """Run all examples."""
    
    print("\n" + "🤖" * 30)
    print("AGENT STAMINA: OpenClaw Self-Monitoring Examples")
    print("🤖" * 30 + "\n")
    
    example_basic_monitoring()
    example_context_manager()
    example_decorator()
    example_periodic_checkpoints()
    example_error_handling()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
    print("\n💡 Tips for real usage:")
    print("   1. Call monitor_me() at the start of your session")
    print("   2. Use stamina_snapshot() after major phases")
    print("   3. Check should_checkpoint() before long operations")
    print("   4. Use StaminaContext for complex multi-step tasks")
    print("   5. Review stamina_report() before finishing")
    print()
