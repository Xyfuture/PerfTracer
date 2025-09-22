#!/usr/bin/env python3
"""Demonstrate the record_event context manager with real time data."""

from __future__ import annotations

import time
from pathlib import Path

from perf_tracer import PerfettoTracer


def cycles_from_perf_counter() -> float:
    return float(time.perf_counter_ns())


def main() -> None:
    tracer = PerfettoTracer(ns_per_cycle=1.0)
    module = tracer.register_module("sleep-demo")
    track = tracer.register_track("worker", module)

    print("Recording sleeps with record_event() ...")

    with tracer.record_event(track, cycles_from_perf_counter, "sleep_500ms"):
        time.sleep(0.5)

    with tracer.record_event(track, cycles_from_perf_counter, "sleep_100ms"):
        time.sleep(0.1)

    output_path = Path(__file__).with_name("record_event_trace.json")
    tracer.save(output_path.as_posix(), display_time_unit="ms")

    print(f"Trace saved to {output_path}. Load it in https://ui.perfetto.dev to inspect the spans.")


if __name__ == "__main__":
    main()

