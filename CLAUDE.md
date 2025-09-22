# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PerfTracer is a Python library for generating Perfetto-compatible trace files. It creates Chrome Trace Event JSON format files that can be analyzed using Perfetto (ui.perfetto.dev) for performance analysis and visualization.

## Key Architecture

- **Main Class**: `PerfettoTracer` in `src/perf_tracer/tracer.py` - handles all tracing functionality
- **Time Units**: All external APIs use "cycles" as time units, converted internally to microseconds via `ns_per_cycle` parameter
- **Module/Track System**: Three-tier hierarchy: modules (processes) → tracks (threads) → sub-tracks (categories)
  - Modules get unique process IDs (pid) starting from 100000
  - Tracks get unique thread IDs (tid) starting from 1000
  - Sub-tracks use same tid but different categories for slice grouping
- **Event Types**:
  - Complete events (X): Single events with start/duration
  - Scoped events (B/E): Begin/End pairs that must be properly nested
- **Global Instance**: Supports singleton pattern via `init_global_tracer()` and `get_global_tracer()`

## Development Commands

**Installation (development mode):**
```bash
pip install -e .
```

**Run tests:**
```bash
pytest tests/
```

**Run tests with coverage:**
```bash
pytest tests/ --cov=src/perf_tracer --cov-report=html --cov-report=term-missing
```

**Format code:**
```bash
black src/ tests/ examples/
```

**Sort imports:**
```bash
isort src/ tests/ examples/
```

**Type checking:**
```bash
mypy src/
```

**Lint code:**
```bash
flake8 src/ tests/ examples/
```

## Core Usage Pattern

1. Create tracer with time scale: `tracer = PerfettoTracer(ns_per_cycle=0.5)`
2. Register modules/tracks: `module = tracer.register_module("cpu")` then `track = tracer.register_track("ALU", module)`
3. Add events: `tracer.complete_event(track, "operation", start_ts, end_ts)`
4. Save trace: `tracer.save("trace.json")`
5. Analyze in Perfetto: Upload to ui.perfetto.dev

## Key Constraints

- Scoped events must be properly nested (stack-based) within each track
- All time parameters in public APIs are in cycles (converted to microseconds internally)
- Module names and track names must be unique within their scope
- Process metadata is automatically added when registering modules/tracks
- Supports context manager (`record_event`) for automatic begin/end tracking
- Default module "default" is created automatically if no module is specified