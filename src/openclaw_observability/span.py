"""
Span data structures for tracing.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid


class SpanType(str, Enum):
    """Types of traced operations."""
    AGENT_DECISION = "agent_decision"
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    FUNCTION = "function"
    ORCHESTRATION = "orchestration"
    DATA_PROCESSING = "data_processing"


class SpanStatus(str, Enum):
    """Execution status of a span."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RUNNING = "running"


@dataclass
class LLMCall:
    """Details of an LLM API call."""
    model: str
    prompt: str
    response: str
    tokens: dict[str, int]
    latency_ms: float
    cost: Optional[float] = None
    temperature: Optional[float] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Span:
    """A single traced operation."""
    span_id: str = field(default_factory=lambda: f"span_{uuid.uuid4().hex[:12]}")
    trace_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    name: str = ""
    span_type: SpanType = SpanType.FUNCTION
    status: SpanStatus = SpanStatus.RUNNING
    
    # Timing
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    
    # Data
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # LLM-specific
    llm_calls: list[LLMCall] = field(default_factory=list)
    
    # Error tracking
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    # Agent context
    agent_id: Optional[str] = None
    framework: Optional[str] = None
    
    def complete(self, outputs: Optional[dict] = None, error: Optional[Exception] = None):
        """Mark span as complete."""
        self.end_time = datetime.utcnow()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        
        if error:
            self.status = SpanStatus.ERROR
            self.error = str(error)
            self.error_type = type(error).__name__
        else:
            self.status = SpanStatus.SUCCESS
            
        if outputs:
            self.outputs = outputs
    
    def add_llm_call(self, llm_call: LLMCall):
        """Add an LLM call to this span."""
        self.llm_calls.append(llm_call)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        data = {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "span_type": self.span_type.value,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "metadata": self.metadata,
            "llm_calls": [call.to_dict() for call in self.llm_calls],
            "error": self.error,
            "error_type": self.error_type,
            "agent_id": self.agent_id,
            "framework": self.framework,
        }
        return data
