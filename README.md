# PerfTracer

A Python library for generating Perfetto-compatible trace files.

## Features

- Generate Chrome Trace Event JSON format compatible with Perfetto
- Support for scoped events (begin/end) and complete events
- Configurable time units and cycles
- Easy-to-use API for performance tracing

## Installation

```bash
git clone https://github.com/Xyfuture/PerfTracer.git
cd PerfTracer
pip install -e . 
```

## Quick Start

```python
from perf_tracer import PerfettoTracer

# Create tracer with custom settings
tracer = PerfettoTracer(process_name="MySim", ns_per_cycle=0.5)

# Register units/tracks
alu = tracer.register_unit("ALU")
fpu = tracer.register_unit("FPU")

# Add events
tracer.complete_event(alu, "issue", start_cycles=100, end_cycles=150)
tracer.start_event(alu, "execute", start_cycles=150)
tracer.end_event(alu, end_cycles=200)

# Save trace
tracer.save("trace.json")
```

## API Reference

### PerfettoTracer

Main class for creating and managing trace events.

#### Methods

- `register_unit(unit_name: str) -> int` - Register a new unit/track
- `start_event(tid_or_unit, name: str, ts_cycles: float)` - Start a scoped event
- `end_event(tid_or_unit, ts_cycles: float, name: str = None)` - End a scoped event
- `complete_event(tid_or_unit, name: str, start_ts: float, end_ts: float = None, dur: float = None)` - Add a complete event
- `save(path: str, display_time_unit: str = "ns")` - Save trace to file

## Usage with Perfetto

1. Generate a trace file using this library
2. Open [ui.perfetto.dev](https://ui.perfetto.dev)
3. Upload your trace file for analysis

## License

MIT License