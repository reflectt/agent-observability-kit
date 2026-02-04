"""
OpenClaw Observability Toolkit - Universal Agent Tracing

Framework-agnostic observability for AI agents.
"""

from .tracer import Tracer, observe, trace, get_current_trace, init_tracer, get_tracer
from .storage import TraceStorage, FileStorage
from .span import Span, SpanType, SpanStatus

__version__ = "0.1.0"
__all__ = [
    "Tracer",
    "observe",
    "trace",
    "get_current_trace",
    "init_tracer",
    "get_tracer",
    "TraceStorage",
    "FileStorage",
    "Span",
    "SpanType",
    "SpanStatus",
]
