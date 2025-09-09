"""
Example usage of PerfTracer.
"""

from perf_tracer import PerfettoTracer


def main():
    """Example demonstrating basic usage of PerfettoTracer."""
    # Create tracer with custom settings
    tracer = PerfettoTracer(
        process_name="MySimulator",
        ns_per_cycle=0.5,  # 1 cycle = 0.5 ns
        pid=1
    )
    
    # Register units/tracks
    alu = tracer.register_unit("ALU")
    fpu = tracer.register_unit("FPU")
    memory = tracer.register_unit("Memory")
    
    # Add complete events
    tracer.complete_event(alu, "add_operation", start_ts=100, end_ts=150)
    tracer.complete_event(fpu, "mul_operation", start_ts=120, end_ts=180)
    tracer.complete_event(memory, "load", start_ts=80, end_ts=110)
    tracer.complete_event(memory, "store", start_ts=160, end_ts=190)
    
    # Add scoped events
    tracer.start_event(alu, "complex_calculation", start_ts=200)
    tracer.start_event(fpu, "sqrt_operation", start_ts=210)
    tracer.end_event(fpu, end_ts=230)
    tracer.end_event(alu, end_ts=250)
    
    # Save the trace
    tracer.save("example_trace.json")
    print("Trace saved to example_trace.json")
    print("Open https://ui.perfetto.dev to analyze the trace")


if __name__ == "__main__":
    main()