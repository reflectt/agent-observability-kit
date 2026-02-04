"""
OpenClaw native integration.
"""

from typing import Callable
from ..tracer import observe
from ..span import SpanType


def openclaw_observe(func: Callable) -> Callable:
    """
    Decorator for OpenClaw agent functions.
    
    Automatically detects function type and applies appropriate span type.
    
    Usage:
        @openclaw_observe
        def my_agent_function(input):
            return process(input)
    """
    # Detect function type from name patterns
    func_name = func.__name__.lower()
    
    if any(keyword in func_name for keyword in ["decide", "choose", "plan", "agent"]):
        span_type = SpanType.AGENT_DECISION
    elif any(keyword in func_name for keyword in ["call", "invoke", "execute", "run"]):
        span_type = SpanType.ORCHESTRATION
    elif any(keyword in func_name for keyword in ["tool", "function", "action"]):
        span_type = SpanType.TOOL_CALL
    else:
        span_type = SpanType.FUNCTION
    
    return observe(span_type=span_type)(func)
