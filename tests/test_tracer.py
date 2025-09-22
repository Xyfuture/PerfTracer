"""Tests for the PerfettoTracer core behaviours."""

from __future__ import annotations

import json
from typing import Iterator

import pytest

from perf_tracer import PerfettoTracer


def test_register_module_and_track_metadata() -> None:
    tracer = PerfettoTracer(ns_per_cycle=2.0)

    module = tracer.register_module("core")
    track = tracer.register_track("worker", module)

    assert module.module_name == "core"
    assert track.module_name == "core"
    assert track.pid == module.pid
    assert track.tid >= 1000
    assert tracer.list_modules() == ["core"]
    assert tracer.list_tracks() == ["core.worker"]

    module_event, thread_event = tracer._events[:2]
    assert module_event == {
        "ph": "M",
        "pid": module.pid,
        "name": "process_name",
        "args": {"name": "core"},
    }
    assert thread_event == {
        "ph": "M",
        "pid": module.pid,
        "tid": track.tid,
        "name": "thread_name",
        "args": {"name": "worker"},
    }

    # Should return same module when registering again
    same_module = tracer.register_module("core")
    assert same_module == module


def test_register_track_without_module_uses_defaults() -> None:
    tracer = PerfettoTracer()

    track = tracer.register_track("io")

    assert track.module_name == "default"
    assert track.pid == 100000
    assert tracer.list_tracks() == ["default.io"]
    assert tracer._open_events[track] == []

    # Should return same track when registering again
    same_track = tracer.register_track("io")
    assert same_track == track




def test_start_and_end_event_nested_stack() -> None:
    tracer = PerfettoTracer(ns_per_cycle=50.0)
    track = tracer.register_track("runner")

    tracer.start_event(track, ts_cycles=10.0, event_name="outer")
    tracer.start_event(track, ts_cycles=20.0, event_name="inner")
    tracer.end_event(track, ts_cycles=40.0)
    tracer.end_event(track, ts_cycles=60.0)

    assert tracer._open_events[track] == []

    b1, b2, e1, e2 = tracer._events[-4:]
    assert [event["ph"] for event in (b1, b2, e1, e2)] == ["B", "B", "E", "E"]
    assert b1["name"] == "outer"
    assert b2["name"] == "inner"
    assert b1["ts"] == pytest.approx(0.5)
    assert b2["ts"] == pytest.approx(1.0)
    assert e1["ts"] == pytest.approx(2.0)
    assert e2["ts"] == pytest.approx(3.0)


def test_end_event_name_mismatch_raises() -> None:
    tracer = PerfettoTracer()
    track = tracer.register_track("runner")

    tracer.start_event(track, ts_cycles=1.0, event_name="outer")

    with pytest.raises(ValueError):
        tracer.end_event(track, ts_cycles=2.0, name="inner")

    assert tracer._open_events[track]


def test_complete_event_with_end_ts_and_dur() -> None:
    tracer = PerfettoTracer(ns_per_cycle=10.0)
    track = tracer.register_track("runner")

    tracer.complete_event(track, start_ts=100.0, end_ts=160.0, name="calc")
    event_from_end = tracer._events[-1]

    tracer.complete_event(track, start_ts=200.0, dur=80.0, name="calc_dur")
    event_from_dur = tracer._events[-1]

    assert event_from_end["dur"] == pytest.approx(0.6)
    assert event_from_dur["dur"] == pytest.approx(0.8)
    assert event_from_end["ts"] == pytest.approx(1.0)
    assert event_from_dur["ts"] == pytest.approx(2.0)

    with pytest.raises(ValueError):
        tracer.complete_event(track, start_ts=0.0, end_ts=10.0, dur=5.0, name="bad")

    with pytest.raises(ValueError):
        tracer.complete_event(track, start_ts=100.0, end_ts=50.0, name="negative")


def test_record_event_context_manager() -> None:
    tracer = PerfettoTracer()
    track = tracer.register_track("ctx")

    time_values: Iterator[float] = iter([1000.0, 1600.0])

    def fake_time() -> float:
        return next(time_values)

    with tracer.record_event(track, fake_time, "scoped"):
        pass

    begin_event, end_event = tracer._events[-2:]
    assert begin_event["ph"] == "B"
    assert end_event["ph"] == "E"
    assert begin_event["name"] == "scoped"
    assert begin_event["ts"] == pytest.approx(1.0)
    assert end_event["ts"] == pytest.approx(1.6)


def test_save_outputs_tracefile(tmp_path) -> None:
    tracer = PerfettoTracer()
    track = tracer.register_track("io")
    tracer.complete_event(track, start_ts=0.0, dur=100.0, name="write")

    output_path = tmp_path / "trace.json"
    tracer.save(str(output_path), display_time_unit="us")

    with output_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    assert data["displayTimeUnit"] == "us"
    assert len(data["traceEvents"]) >= 3


def test_global_tracer_helpers() -> None:
    PerfettoTracer._global_instance = None

    with pytest.raises(RuntimeError):
        PerfettoTracer.get_global_tracer()

    tracer = PerfettoTracer.init_global_tracer(ns_per_cycle=5.0)
    assert tracer.ns_per_cycle == 5.0
    assert PerfettoTracer.get_global_tracer() is tracer

    PerfettoTracer._global_instance = None

