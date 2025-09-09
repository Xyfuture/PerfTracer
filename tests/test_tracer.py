"""
Basic tests for PerfTracer.
"""

import pytest
import tempfile
import os
from perf_tracer import PerfettoTracer


def test_tracer_initialization():
    """Test that the tracer initializes with default values."""
    tracer = PerfettoTracer()
    assert tracer.process_name == "Simulator"
    assert tracer.ns_per_cycle == 1.0
    assert tracer.pid == 1


def test_tracer_custom_initialization():
    """Test that the tracer initializes with custom values."""
    tracer = PerfettoTracer(process_name="Custom", ns_per_cycle=0.5, pid=2)
    assert tracer.process_name == "Custom"
    assert tracer.ns_per_cycle == 0.5
    assert tracer.pid == 2


def test_register_unit():
    """Test unit registration."""
    tracer = PerfettoTracer()
    tid = tracer.register_unit("ALU")
    assert tid == 1000
    assert tracer._unit_to_tid["ALU"] == tid


def test_register_duplicate_unit():
    """Test that registering the same unit returns the same tid."""
    tracer = PerfettoTracer()
    tid1 = tracer.register_unit("ALU")
    tid2 = tracer.register_unit("ALU")
    assert tid1 == tid2


def test_complete_event():
    """Test complete event creation."""
    tracer = PerfettoTracer()
    tid = tracer.register_unit("ALU")
    tracer.complete_event(tid, "test_event", 100, 200)
    assert len(tracer._events) == 3  # process metadata + thread metadata + event


def test_save_trace():
    """Test saving trace to file."""
    tracer = PerfettoTracer()
    tid = tracer.register_unit("ALU")
    tracer.complete_event(tid, "test_event", 100, 200)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        tracer.save(temp_path)
        assert os.path.exists(temp_path)
        
        # Check file contents
        with open(temp_path, 'r') as f:
            import json
            data = json.load(f)
            assert "traceEvents" in data
            assert "displayTimeUnit" in data
            assert len(data["traceEvents"]) > 0
    finally:
        os.unlink(temp_path)