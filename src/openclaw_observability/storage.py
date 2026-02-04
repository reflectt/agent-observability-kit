"""
Trace storage backends.
"""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

from .span import Span


class TraceStorage(ABC):
    """Abstract interface for trace storage."""
    
    @abstractmethod
    def save_span(self, span: Span):
        """Save a span to storage."""
        pass
    
    @abstractmethod
    def finalize_trace(self, trace_id: str):
        """Finalize a trace (all spans complete)."""
        pass
    
    @abstractmethod
    def get_trace(self, trace_id: str) -> dict:
        """Retrieve a complete trace."""
        pass
    
    @abstractmethod
    def list_traces(self, limit: int = 100) -> list[dict]:
        """List recent traces."""
        pass


class FileStorage(TraceStorage):
    """Simple file-based storage for traces."""
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.openclaw/traces"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create index file if doesn't exist
        self.index_file = self.base_dir / "index.json"
        if not self.index_file.exists():
            self.index_file.write_text(json.dumps({"traces": []}))
    
    def _get_trace_dir(self, trace_id: str) -> Path:
        """Get directory for a trace."""
        trace_dir = self.base_dir / trace_id
        trace_dir.mkdir(exist_ok=True)
        return trace_dir
    
    def save_span(self, span: Span):
        """Save a span to a JSON file."""
        trace_dir = self._get_trace_dir(span.trace_id)
        span_file = trace_dir / f"{span.span_id}.json"
        
        span_data = span.to_dict()
        with open(span_file, "w") as f:
            json.dump(span_data, f, indent=2)
    
    def finalize_trace(self, trace_id: str):
        """Mark trace as complete and update index."""
        trace_dir = self._get_trace_dir(trace_id)
        
        # Load all spans
        spans = []
        for span_file in sorted(trace_dir.glob("*.json")):
            with open(span_file) as f:
                spans.append(json.load(f))
        
        # Create trace summary
        if spans:
            root_span = next((s for s in spans if s["parent_span_id"] is None), spans[0])
            summary = {
                "trace_id": trace_id,
                "name": root_span["name"],
                "start_time": min(s["start_time"] for s in spans),
                "end_time": max(s["end_time"] for s in spans if s["end_time"]),
                "total_duration_ms": sum(s["duration_ms"] or 0 for s in spans),
                "span_count": len(spans),
                "status": "error" if any(s["status"] == "error" for s in spans) else "success",
                "agent_id": root_span.get("agent_id"),
                "framework": root_span.get("framework"),
            }
            
            # Update index
            with open(self.index_file, "r+") as f:
                index = json.load(f)
                # Remove old entry if exists
                index["traces"] = [t for t in index["traces"] if t["trace_id"] != trace_id]
                # Add new entry at beginning
                index["traces"].insert(0, summary)
                # Keep only last 1000 traces in index
                index["traces"] = index["traces"][:1000]
                f.seek(0)
                f.truncate()
                json.dump(index, f, indent=2)
    
    def get_trace(self, trace_id: str) -> dict:
        """Load a complete trace with all spans."""
        trace_dir = self._get_trace_dir(trace_id)
        
        spans = []
        for span_file in sorted(trace_dir.glob("*.json")):
            with open(span_file) as f:
                spans.append(json.load(f))
        
        if not spans:
            return {"trace_id": trace_id, "spans": [], "error": "Trace not found"}
        
        # Build trace structure
        root_span = next((s for s in spans if s["parent_span_id"] is None), spans[0])
        
        return {
            "trace_id": trace_id,
            "name": root_span["name"],
            "spans": spans,
            "metadata": {
                "span_count": len(spans),
                "total_duration_ms": sum(s["duration_ms"] or 0 for s in spans),
                "agent_id": root_span.get("agent_id"),
                "framework": root_span.get("framework"),
            }
        }
    
    def list_traces(self, limit: int = 100) -> list[dict]:
        """List recent traces from index."""
        with open(self.index_file) as f:
            index = json.load(f)
            return index["traces"][:limit]
