"""Basic usage for generating a Perfetto trace with PerfettoTracer."""

from __future__ import annotations

from pathlib import Path

from perf_tracer import PerfettoTracer


def main() -> None:
    tracer = PerfettoTracer(ns_per_cycle=2.5)

    cpu_module = tracer.register_module("cpu")
    fetch_track = tracer.register_track("fetch", cpu_module)
    execute_track = tracer.register_track("execute", cpu_module)
    execute_stage = tracer.register_sub_track(execute_track, "alu")

    tracer.complete_event(fetch_track, "fetch_instruction", start_ts=0.0, dur=120.0)
    tracer.complete_event(execute_track, "decode", start_ts=80.0, dur=140.0)

    tracer.start_event(execute_stage, "alu_window", ts_cycles=260.0)
    tracer.end_event(execute_stage, ts_cycles=520.0)

    trace_path = Path(__file__).with_name("basic_trace.json")
    tracer.save(trace_path.as_posix())
    print(f"Trace saved to {trace_path}. Import it at https://ui.perfetto.dev")


if __name__ == "__main__":
    main()

