#!/usr/bin/env python3
"""
Example demonstrating the record_event function with a 5-second sleep.
"""

import time
from perf_tracer.tracer import PerfettoTracer

def get_time_cycles() -> float:
    """Return current time in nanoseconds for cycles."""
    return time.time_ns()

def main():
    # Initialize tracer
    tracer = PerfettoTracer(
        process_name="SleepExample",
        ns_per_cycle=1.0,  # 1 cycle = 1 nanosecond
        pid=1
    )

    # Register a unit/track
    sleep_unit = tracer.register_unit("SleepOperations")

    print("Starting 5-second sleep test...")
    print("This will record the sleep operation using record_event context manager")

    # Record a 5-second sleep event using the context manager
    with tracer.record_event(sleep_unit, "5_second_sleep", get_time_cycles):
        print("  - Sleeping for 5 seconds...")
        time.sleep(5)
        print("  - Sleep completed!")

    # Add another event for comparison
    with tracer.record_event(sleep_unit, "short_sleep", get_time_cycles):
        print("  - Sleeping for 1 second...")
        time.sleep(1)
        print("  - Short sleep completed!")

    # Save the trace
    output_file = "sleep_trace.json"
    tracer.save(output_file)
    print(f"\nTrace saved to {output_file}")
    print("You can open this file in ui.perfetto.dev to visualize the timing")

    # Print summary
    print(f"\nSummary:")
    print(f"- Process: {tracer.process_name}")
    print(f"- Total events recorded: {len(tracer._events) - 2}")  # Subtract metadata events
    print(f"- Time unit: {tracer.ns_per_cycle} ns/cycle")
    print(f"- Output file: {output_file}")

if __name__ == "__main__":
    main()