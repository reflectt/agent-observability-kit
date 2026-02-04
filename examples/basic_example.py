"""
Basic example showing framework-agnostic tracing.
"""

import time
import random
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openclaw_observability import observe, trace, init_tracer, get_tracer
from openclaw_observability.span import SpanType


# Initialize tracer
tracer = init_tracer(agent_id="demo-agent")


@observe(span_type=SpanType.AGENT_DECISION)
def analyze_sentiment(text: str) -> dict:
    """Simulated sentiment analysis."""
    time.sleep(0.1)  # Simulate processing
    
    # Simulate LLM call
    tracer.add_llm_call(
        model="claude-3-5-sonnet",
        prompt=f"Analyze sentiment of: {text}",
        response="The sentiment is positive with 0.85 confidence.",
        tokens={"input": 50, "output": 20, "total": 70},
        latency_ms=100,
        cost=0.001,
    )
    
    return {
        "sentiment": "positive",
        "confidence": 0.85,
        "text": text,
    }


@observe(span_type=SpanType.TOOL_CALL)
def fetch_user_data(user_id: str) -> dict:
    """Simulated database lookup."""
    time.sleep(0.05)
    return {
        "user_id": user_id,
        "name": "John Doe",
        "tier": "premium",
    }


@observe(span_type=SpanType.ORCHESTRATION)
def process_customer_query(query: str, user_id: str) -> dict:
    """Main agent workflow."""
    # Step 1: Fetch user context
    user_data = fetch_user_data(user_id)
    
    # Step 2: Analyze query sentiment
    sentiment = analyze_sentiment(query)
    
    # Step 3: Simulate response generation
    time.sleep(0.1)
    tracer.add_llm_call(
        model="claude-3-5-sonnet",
        prompt=f"Generate response for {user_data['tier']} user with {sentiment['sentiment']} query: {query}",
        response="Thank you for your positive feedback! As a premium member, you get priority support.",
        tokens={"input": 120, "output": 25, "total": 145},
        latency_ms=150,
        cost=0.002,
    )
    
    return {
        "response": "Thank you for your positive feedback! As a premium member, you get priority support.",
        "sentiment": sentiment,
        "user_tier": user_data["tier"],
    }


def run_demo():
    """Run demo traces."""
    print("🔍 OpenClaw Observability - Basic Example")
    print("=" * 50)
    
    # Example 1: Successful trace
    with trace("customer_query_success"):
        result = process_customer_query(
            query="Your product is amazing!",
            user_id="user_123"
        )
        print(f"✅ Success: {result['response']}")
    
    # Example 2: Failed trace
    with trace("customer_query_error"):
        try:
            # Simulate an error
            user_data = fetch_user_data("invalid_user")
            raise ValueError("User not found in database")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Example 3: Multiple operations
    with trace("batch_processing"):
        queries = [
            "Love your service!",
            "Having some issues",
            "Quick question about pricing",
        ]
        for i, query in enumerate(queries):
            result = process_customer_query(query, f"user_{i}")
            print(f"  {i+1}. Processed: {query[:30]}...")
    
    print("=" * 50)
    print(f"📊 Generated traces stored in: ~/.openclaw/traces/")
    print(f"🌐 View at: http://localhost:5000")
    print("\nRun: python server/app.py")


if __name__ == "__main__":
    run_demo()
