"""
LangChain integration example (requires langchain).

Install: pip install langchain openai
"""

import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from langchain.llms import OpenAI
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️  LangChain not installed. Run: pip install langchain openai")
    sys.exit(1)

from openclaw_observability import init_tracer, trace
from openclaw_observability.integrations import LangChainCallbackHandler


def run_langchain_example():
    """Example showing LangChain integration."""
    print("🔍 OpenClaw Observability - LangChain Example")
    print("=" * 50)
    
    # Initialize observability
    tracer = init_tracer(agent_id="langchain-demo")
    callback_handler = LangChainCallbackHandler(agent_id="langchain-demo")
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Set OPENAI_API_KEY to run this example")
        print("\nDemo mode: Showing how integration works...")
        print("""
# Real usage:
callback_handler = LangChainCallbackHandler(agent_id="my-agent")

llm = OpenAI(temperature=0.7)
chain = LLMChain(
    llm=llm,
    prompt=PromptTemplate.from_template("Summarize: {text}"),
    callbacks=[callback_handler]  # ← Automatic tracing!
)

result = chain.run(text="Your input here")
        """)
        return
    
    # Create LangChain components
    llm = OpenAI(temperature=0.7)
    prompt = PromptTemplate(
        input_variables=["topic"],
        template="Write a short poem about {topic}:"
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    
    # Run with observability
    with trace("langchain_poem_generation"):
        result = chain.run(
            topic="AI agents",
            callbacks=[callback_handler]
        )
        print(f"✅ Generated poem:\n{result}")
    
    print("=" * 50)
    print(f"📊 Trace stored in: ~/.openclaw/traces/")
    print(f"🌐 View at: http://localhost:5000")


if __name__ == "__main__":
    run_langchain_example()
