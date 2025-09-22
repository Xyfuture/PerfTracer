# Repository Guidelines

## Project Structure & Module Organization
Core library code lives in `src/perf_tracer`, with `tracer.py` exposing `PerfettoTracer` and helper utilities. Tests reside under `tests/`, mirroring the public API via Pytest cases such as `tests/test_tracer.py`. Example scripts in `examples/` demonstrate typical trace collection flows (see `examples/basic_usage.py`). Documentation stubs live under `docs/`, and project metadata plus tooling configuration sit in `pyproject.toml` and `README.md`.

## Build, Test, and Development Commands
Install the project in editable mode with `pip install -e .` to pick up local changes. Run `pytest` for the default test suite, or `pytest --cov=src/perf_tracer --cov-report=term-missing` to inspect coverage gaps. Apply formatters with `black src/ tests/ examples/` and `isort src/ tests/ examples/ --profile black`. Execute `mypy src/` to enforce static typing expectations.

## Coding Style & Naming Conventions
Code targets Python 3.8+, uses four-space indentation, and keeps lines within 88 characters (Black defaults). Public functions require precise type hints and concise docstrings. Follow `snake_case` for modules and functions, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Preserve existing parameter names and cycle-based timing semantics when extending the API.

## Testing Guidelines
Tests use Pytest with discovery patterns `tests/test_*.py`, `Test*` classes, and `test_*` functions. Prefer temporary files (e.g., `tempfile.NamedTemporaryFile`) for trace outputs to keep runs fast. Add focused regression tests alongside new features, ensuring core paths in `src/perf_tracer/tracer.py` remain covered.

## Commit & Pull Request Guidelines
Write imperative, scoped commit messages such as `tracer: add record_event`. Pull requests should describe the change, state the rationale, reference related issues, and note any docs or example updates. Always run formatting, tests, type checks, and coverage commands before requesting review. Avoid committing generated trace artifacts; instead, document the command sequence for reproducing them.

## Architecture Notes
Event recording supports complete (`X`) and scoped (`B`/`E`) events, converting externally supplied cycles into microseconds via `ns_per_cycle`. Track identifiers map to thread-like units starting at 1000. Use `init_global_tracer()` and `get_global_tracer()` helpers when a shared tracer instance simplifies integration.
