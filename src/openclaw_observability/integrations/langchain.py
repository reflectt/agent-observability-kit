"""
LangChain integration for automatic tracing.
"""

from typing import Any, Dict, List, Optional
import time

try:
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.schema import AgentAction, AgentFinish, LLMResult
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseCallbackHandler = object

from ..tracer import get_tracer
from ..span import SpanType, LLMCall


class LangChainCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback handler for automatic observability.
    
    Usage:
        from openclaw.observability.integrations import LangChainCallbackHandler
        
        handler = LangChainCallbackHandler(agent_id="my-agent")
        agent.run("query", callbacks=[handler])
    """
    
    def __init__(self, agent_id: Optional[str] = None):
        self.agent_id = agent_id
        self.tracer = get_tracer()
        self.tracer.agent_id = agent_id
        self.tracer.framework = "langchain"
        
        self._llm_start_times: Dict[str, float] = {}
        self._spans: Dict[str, Any] = {}
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any,
    ) -> None:
        """Track LLM call start."""
        run_id = kwargs.get("run_id", str(id(prompts)))
        self._llm_start_times[run_id] = time.time()
        
        # Start a span for this LLM call
        span = self.tracer.start_span(
            name=f"LLM: {serialized.get('name', 'unknown')}",
            span_type=SpanType.LLM_CALL,
            inputs={"prompts": prompts},
            metadata={"model": serialized.get("name", "unknown")},
        )
        self._spans[run_id] = span
    
    def on_llm_end(
        self,
        response: LLMResult,
        **kwargs: Any,
    ) -> None:
        """Track LLM call completion."""
        run_id = kwargs.get("run_id", "")
        start_time = self._llm_start_times.pop(run_id, time.time())
        latency_ms = (time.time() - start_time) * 1000
        
        # Extract response text
        responses = []
        for generation_list in response.generations:
            for generation in generation_list:
                responses.append(generation.text)
        
        # Get token usage
        tokens = {}
        if hasattr(response, "llm_output") and response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})
            tokens = {
                "input": token_usage.get("prompt_tokens", 0),
                "output": token_usage.get("completion_tokens", 0),
                "total": token_usage.get("total_tokens", 0),
            }
        
        # Record LLM call
        span = self._spans.pop(run_id, None)
        if span:
            self.tracer.end_span(
                span,
                outputs={"responses": responses, "tokens": tokens},
            )
    
    def on_llm_error(
        self,
        error: Exception,
        **kwargs: Any,
    ) -> None:
        """Track LLM errors."""
        run_id = kwargs.get("run_id", "")
        self._llm_start_times.pop(run_id, None)
        
        span = self._spans.pop(run_id, None)
        if span:
            self.tracer.end_span(span, error=error)
    
    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Track chain execution start."""
        run_id = kwargs.get("run_id", str(id(inputs)))
        
        span = self.tracer.start_span(
            name=f"Chain: {serialized.get('name', 'unknown')}",
            span_type=SpanType.ORCHESTRATION,
            inputs=inputs,
        )
        self._spans[run_id] = span
    
    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Track chain execution end."""
        run_id = kwargs.get("run_id", "")
        span = self._spans.pop(run_id, None)
        if span:
            self.tracer.end_span(span, outputs=outputs)
    
    def on_chain_error(
        self,
        error: Exception,
        **kwargs: Any,
    ) -> None:
        """Track chain errors."""
        run_id = kwargs.get("run_id", "")
        span = self._spans.pop(run_id, None)
        if span:
            self.tracer.end_span(span, error=error)
    
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Track tool execution start."""
        run_id = kwargs.get("run_id", str(id(input_str)))
        
        span = self.tracer.start_span(
            name=f"Tool: {serialized.get('name', 'unknown')}",
            span_type=SpanType.TOOL_CALL,
            inputs={"input": input_str},
        )
        self._spans[run_id] = span
    
    def on_tool_end(
        self,
        output: str,
        **kwargs: Any,
    ) -> None:
        """Track tool execution end."""
        run_id = kwargs.get("run_id", "")
        span = self._spans.pop(run_id, None)
        if span:
            self.tracer.end_span(span, outputs={"output": output})
    
    def on_tool_error(
        self,
        error: Exception,
        **kwargs: Any,
    ) -> None:
        """Track tool errors."""
        run_id = kwargs.get("run_id", "")
        span = self._spans.pop(run_id, None)
        if span:
            self.tracer.end_span(span, error=error)
    
    def on_agent_action(
        self,
        action: AgentAction,
        **kwargs: Any,
    ) -> None:
        """Track agent decisions."""
        span = self.tracer.start_span(
            name=f"Agent Action: {action.tool}",
            span_type=SpanType.AGENT_DECISION,
            inputs={
                "tool": action.tool,
                "tool_input": action.tool_input,
                "log": action.log,
            },
        )
        # Will be closed by tool execution
    
    def on_agent_finish(
        self,
        finish: AgentFinish,
        **kwargs: Any,
    ) -> None:
        """Track agent completion."""
        # Agent trace complete
        pass
