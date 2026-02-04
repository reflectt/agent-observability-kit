"""
Tests for core tracing functionality.
"""

import pytest
import time
from pathlib import Path
import sys
import tempfile
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openclaw_observability import (
    Tracer, observe, trace, init_tracer,
    FileStorage, SpanType, SpanStatus
)


@pytest.fixture
def temp_storage():
    """Create temporary storage for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield FileStorage(base_dir=tmpdir)


def test_basic_trace(temp_storage):
    """Test creating a basic trace."""
    tracer = Tracer(storage=temp_storage, agent_id="test-agent")
    
    trace_id = tracer.start_trace("test_trace")
    assert trace_id.startswith("tr_")
    
    tracer.end_trace()


def test_span_creation(temp_storage):
    """Test creating spans."""
    tracer = Tracer(storage=temp_storage)
    
    trace_id = tracer.start_trace("test")
    span = tracer.start_span("test_span", span_type=SpanType.FUNCTION)
    
    assert span.trace_id == trace_id
    assert span.name == "test_span"
    assert span.status == SpanStatus.RUNNING
    
    tracer.end_span(span, outputs={"result": "success"})
    assert span.status == SpanStatus.SUCCESS
    assert span.duration_ms is not None


def test_observe_decorator(temp_storage):
    """Test @observe decorator."""
    tracer = init_tracer(storage=temp_storage)
    
    @observe(span_type=SpanType.FUNCTION)
    def add_numbers(a: int, b: int) -> int:
        return a + b
    
    with trace("math_test"):
        result = add_numbers(2, 3)
        assert result == 5
    
    # Verify trace was stored
    traces = temp_storage.list_traces()
    assert len(traces) > 0
    assert traces[0]["name"] == "math_test"


def test_error_handling(temp_storage):
    """Test error capture."""
    tracer = init_tracer(storage=temp_storage)
    
    @observe()
    def failing_function():
        raise ValueError("Test error")
    
    with trace("error_test"):
        try:
            failing_function()
        except ValueError:
            pass
    
    # Verify error was captured
    traces = temp_storage.list_traces()
    trace_data = temp_storage.get_trace(traces[0]["trace_id"])
    
    error_span = next(s for s in trace_data["spans"] if s["error"] is not None)
    assert error_span["status"] == "error"
    assert error_span["error_type"] == "ValueError"


def test_llm_call_tracking(temp_storage):
    """Test LLM call tracking."""
    tracer = init_tracer(storage=temp_storage)
    
    with trace("llm_test"):
        span = tracer.start_span("llm_operation")
        
        tracer.add_llm_call(
            model="test-model",
            prompt="test prompt",
            response="test response",
            tokens={"input": 10, "output": 5},
            latency_ms=100,
            cost=0.001,
        )
        
        tracer.end_span(span)
    
    # Verify LLM call was captured
    traces = temp_storage.list_traces()
    trace_data = temp_storage.get_trace(traces[0]["trace_id"])
    
    span_with_llm = trace_data["spans"][-1]
    assert len(span_with_llm["llm_calls"]) == 1
    assert span_with_llm["llm_calls"][0]["model"] == "test-model"


def test_storage_persistence(temp_storage):
    """Test that traces persist correctly."""
    tracer = Tracer(storage=temp_storage)
    
    trace_id = tracer.start_trace("persistent_trace")
    span = tracer.start_span("test_span")
    tracer.end_span(span, outputs={"data": "test"})
    tracer.end_trace()
    
    # Retrieve trace
    trace_data = temp_storage.get_trace(trace_id)
    
    assert trace_data["trace_id"] == trace_id
    assert len(trace_data["spans"]) == 2  # root + test_span
    assert trace_data["spans"][1]["outputs"]["data"] == "test"


def test_nested_spans(temp_storage):
    """Test nested span relationships."""
    tracer = init_tracer(storage=temp_storage)
    
    @observe()
    def inner_function():
        return "inner"
    
    @observe()
    def outer_function():
        return inner_function()
    
    with trace("nested_test"):
        outer_function()
    
    traces = temp_storage.list_traces()
    trace_data = temp_storage.get_trace(traces[0]["trace_id"])
    
    # Should have root, outer, and inner spans
    assert len(trace_data["spans"]) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
