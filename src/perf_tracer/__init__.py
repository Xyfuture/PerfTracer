"""
PerfTracer: A Python library for generating Perfetto-compatible trace files.

This library provides utilities for creating performance traces that can be
imported and analyzed using Perfetto (ui.perfetto.dev).
"""

from .tracer import PerfettoTracer

__version__ = "0.1.0"
__all__ = ["PerfettoTracer"]