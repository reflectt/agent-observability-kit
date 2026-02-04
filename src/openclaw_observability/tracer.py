"""
Core tracing functionality.
"""

import contextvars
import functools
import inspect
from typing import Any, Callable, Optional
import uuid

from .span import Span, SpanType, LLMCall
from .storage import TraceStorage, FileStorage


# Context variable to track current trace
_current_trace_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_trace_id", default=None
)
_current_span: contextvars.ContextVar[Optional[Span]] = contextvars.ContextVar(
    "current_span", default=None
)


class Tracer:
    """Main tracing interface."""
    
    def __init__(self, storage: Optional[TraceStorage] = None, agent_id: Optional[str] = None):
        self.storage = storage or FileStorage()
        self.agent_id = agent_id
        self.framework = None
    
    def start_trace(self, name: str = "root", metadata: Optional[dict] = None) -> str:
        """Start a new trace."""
        trace_id = f"tr_{uuid.uuid4().hex[:12]}"
        _current_trace_id.set(trace_id)
        
        # Create root span
        root_span = Span(
            trace_id=trace_id,
            name=name,
            span_type=SpanType.ORCHESTRATION,
            agent_id=self.agent_id,
            framework=self.framework,
            metadata=metadata or {},
        )
        _current_span.set(root_span)
        
        return trace_id
    
    def start_span(
        self,
        name: str,
        span_type: SpanType = SpanType.FUNCTION,
        inputs: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> Span:
        """Start a new span within the current trace."""
        trace_id = _current_trace_id.get()
        if not trace_id:
            trace_id = self.start_trace(name="auto_trace")
        
        parent_span = _current_span.get()
        
        span = Span(
            trace_id=trace_id,
            parent_span_id=parent_span.span_id if parent_span else None,
            name=name,
            span_type=span_type,
            inputs=inputs or {},
            metadata=metadata or {},
            agent_id=self.agent_id,
            framework=self.framework,
        )
        
        _current_span.set(span)
        return span
    
    def end_span(self, span: Span, outputs: Optional[dict] = None, error: Optional[Exception] = None):
        """End the current span."""
        span.complete(outputs=outputs, error=error)
        self.storage.save_span(span)
        
        # Restore parent span as current
        if span.parent_span_id:
            # In a real implementation, we'd maintain a span stack
            # For MVP, just clear current span
            _current_span.set(None)
    
    def end_trace(self):
        """End the current trace."""
        trace_id = _current_trace_id.get()
        if trace_id:
            self.storage.finalize_trace(trace_id)
            _current_trace_id.set(None)
            _current_span.set(None)
    
    def add_llm_call(
        self,
        model: str,
        prompt: str,
        response: str,
        tokens: dict[str, int],
        latency_ms: float,
        cost: Optional[float] = None,
    ):
        """Record an LLM API call in the current span."""
        span = _current_span.get()
        if span:
            llm_call = LLMCall(
                model=model,
                prompt=prompt,
                response=response,
                tokens=tokens,
                latency_ms=latency_ms,
                cost=cost,
            )
            span.add_llm_call(llm_call)


# Global tracer instance
_global_tracer: Optional[Tracer] = None


def init_tracer(storage: Optional[TraceStorage] = None, agent_id: Optional[str] = None) -> Tracer:
    """Initialize the global tracer."""
    global _global_tracer
    _global_tracer = Tracer(storage=storage, agent_id=agent_id)
    return _global_tracer


def get_tracer() -> Tracer:
    """Get the global tracer, initializing if needed."""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = Tracer()
    return _global_tracer


def get_current_trace() -> Optional[str]:
    """Get the current trace ID."""
    return _current_trace_id.get()


def observe(
    name: Optional[str] = None,
    span_type: SpanType = SpanType.FUNCTION,
    capture_args: bool = True,
    capture_result: bool = True,
):
    """
    Decorator to automatically trace a function.
    
    Usage:
        @observe(span_type=SpanType.AGENT_DECISION)
        def choose_action(state):
            return action
    """
    def decorator(func: Callable) -> Callable:
        func_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            # Capture inputs
            inputs = {}
            if capture_args:
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                inputs = {k: _serialize_value(v) for k, v in bound.arguments.items()}
            
            # Start span
            span = tracer.start_span(
                name=func_name,
                span_type=span_type,
                inputs=inputs,
            )
            
            try:
                result = func(*args, **kwargs)
                
                # Capture outputs
                outputs = {}
                if capture_result:
                    outputs = {"result": _serialize_value(result)}
                
                tracer.end_span(span, outputs=outputs)
                return result
                
            except Exception as e:
                tracer.end_span(span, error=e)
                raise
        
        return wrapper
    return decorator


def trace(name: str = "trace"):
    """
    Context manager for manual tracing.
    
    Usage:
        with trace("my_operation"):
            # code here
            pass
    """
    class TraceContext:
        def __enter__(self):
            self.tracer = get_tracer()
            self.trace_id = self.tracer.start_trace(name)
            return self.trace_id
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.tracer.end_trace()
    
    return TraceContext()


def _serialize_value(value: Any) -> Any:
    """Serialize a value for storage."""
    # Handle common types
    if value is None or isinstance(value, (int, float, str, bool)):
        return value
    
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    
    # For complex objects, store type and repr
    return {
        "_type": type(value).__name__,
        "_repr": repr(value)[:200],  # Truncate long reprs
    }
