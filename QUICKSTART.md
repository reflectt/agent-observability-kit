# ⚡ OpenClaw Observability - Quick Start Guide

Get visual debugging for your AI agents in **5 minutes**.

---

## 🎯 What This Does

Turns this debugging nightmare:

```python
def agent_function(input):
    print(f"DEBUG: input={input}")  # 🤮
    result = llm.predict(input)
    print(f"DEBUG: result={result}")  # 🤮
    return result
```

Into this:

```python
@observe(span_type=SpanType.AGENT_DECISION)
def agent_function(input):
    result = llm.predict(input)
    return result

# View at: http://localhost:5000
# - See full execution graph
# - Click any step to inspect
# - View LLM prompts/responses
# - Track costs, latency, errors
```

---

## 🚀 5-Minute Setup

### Step 1: Run the Demo (1 min)

```bash
cd projects/observability-toolkit
python3 examples/basic_example.py
```

**Output:**
```
🔍 OpenClaw Observability - Basic Example
==================================================
✅ Success: Thank you for your positive feedback!
❌ Error: User not found in database
  1. Processed: Love your service!...
  2. Processed: Having some issues...
  3. Processed: Quick question about pricing...
==================================================
📊 Generated traces stored in: ~/.openclaw/traces/
🌐 View at: http://localhost:5000
```

✅ You just created 3 traces!

---

### Step 2: Start the Web UI (30 sec)

```bash
python3 server/app.py
```

**Output:**
```
🔍 OpenClaw Observability Server
==================================================
📊 Dashboard: http://localhost:5000
📁 Trace storage: ~/.openclaw/traces/
==================================================
```

---

### Step 3: Open Dashboard (10 sec)

```bash
open http://localhost:5000
```

You'll see:
- **Stats:** Total traces, success rate, avg duration
- **Trace list:** All captured executions
- **Click any trace** to see execution graph

---

### Step 4: Inspect a Trace (2 min)

1. Click on `analyze_sentiment` trace
2. See the execution graph (visual flow)
3. Click on the `analyze_sentiment` span
4. Modal opens showing:
   - **Inputs:** `{"text": "Your product is amazing!"}`
   - **Outputs:** `{"sentiment": "positive", "confidence": 0.85}`
   - **LLM Call:**
     - Prompt: `"Analyze sentiment of: Your product is amazing!"`
     - Response: `"The sentiment is positive with 0.85 confidence."`
     - Tokens: 70 (50 input, 20 output)
     - Cost: $0.001
     - Latency: 100ms

🎉 **You just debugged an agent visually!**

---

## 🔌 Add to Your Code (2 min)

### Option 1: Decorator (easiest)

```python
from openclaw_observability import observe, init_tracer
from openclaw_observability.span import SpanType

# Initialize once
tracer = init_tracer(agent_id="my-agent")

# Decorate your functions
@observe(span_type=SpanType.AGENT_DECISION)
def choose_action(state):
    # Your code here
    return action

@observe(span_type=SpanType.TOOL_CALL)
def fetch_data(query):
    # Your code here
    return data
```

---

### Option 2: Context Manager

```python
from openclaw_observability import trace, get_tracer

tracer = get_tracer()

with trace("my_workflow"):
    # Step 1
    data = fetch_data("query")
    
    # Step 2
    result = process(data)
    
    # Automatically captured!
```

---

### Option 3: LangChain (automatic)

```python
from openclaw_observability.integrations import LangChainCallbackHandler

handler = LangChainCallbackHandler(agent_id="my-agent")

# Add to ANY LangChain call
chain.run(
    input="query",
    callbacks=[handler]  # ← That's it!
)

# All LLM calls, tool invocations, agent decisions
# are automatically traced!
```

---

## 📊 What Gets Captured

Every trace includes:

- ✅ **Execution flow:** Which functions called which
- ✅ **Timing:** How long each step took
- ✅ **Inputs/outputs:** What went in, what came out
- ✅ **LLM calls:** Full prompts, responses, tokens, cost
- ✅ **Errors:** Full exception details
- ✅ **Metadata:** Agent ID, framework, custom tags

---

## 🎨 UI Features

### Dashboard
- **Real-time updates** (auto-refresh every 5s)
- **Quick stats:** Success rate, avg duration, span count
- **Trace list:** Recent executions with status
- **Filters:** (coming soon) By agent, status, date

### Trace Viewer
- **Execution graph:** Visual flow of your agent
- **Span details:** Click any step to inspect
- **LLM calls:** See full prompts/responses
- **Error highlighting:** Failed steps in red
- **Performance metrics:** Duration, tokens, cost

---

## 💡 Common Patterns

### Pattern 1: Multi-Agent System

```python
# Orchestrator
@observe(span_type=SpanType.ORCHESTRATION)
def orchestrate(task):
    data = data_agent.fetch(task)
    analysis = analysis_agent.analyze(data)
    return synthesis_agent.summarize(analysis)

# Specialist agents
@observe(span_type=SpanType.AGENT_DECISION)
def data_agent_fetch(task):
    # ...

@observe(span_type=SpanType.AGENT_DECISION)
def analysis_agent_analyze(data):
    # ...
```

**Result:** See which agent is slow, which failed, cost per agent

---

### Pattern 2: Track LLM Costs

```python
@observe()
def generate_response(prompt):
    response = llm.generate(prompt)
    
    # Record LLM call
    tracer = get_tracer()
    tracer.add_llm_call(
        model="claude-3-5-sonnet",
        prompt=prompt,
        response=response,
        tokens={"input": 100, "output": 50},
        cost=0.0025,  # ← Track cost!
    )
    
    return response
```

**Result:** See total cost in UI, identify expensive operations

---

### Pattern 3: Debug Failures

```python
@observe()
def risky_operation(input):
    try:
        result = process(input)
        return result
    except Exception as e:
        # Exception is automatically captured!
        raise

# In UI: Click failed trace → see full error + stack trace
```

---

## 🔧 Configuration

### Change Storage Location

```python
from openclaw_observability import init_tracer
from openclaw_observability.storage import FileStorage

storage = FileStorage(base_dir="/custom/path/traces")
tracer = init_tracer(storage=storage)
```

### Disable Tracing (production)

```python
import os

if os.getenv("ENABLE_TRACING", "false") == "true":
    tracer = init_tracer(agent_id="my-agent")
else:
    # No-op tracer (zero overhead)
    tracer = None
```

---

## 🐛 Troubleshooting

### "No traces showing in UI"

1. Check storage location: `ls ~/.openclaw/traces/`
2. Verify traces exist: `cat ~/.openclaw/traces/index.json`
3. Restart web server: `python3 server/app.py`

### "ImportError: cannot import name 'init_tracer'"

```bash
# Make sure you're in the project directory
cd projects/observability-toolkit

# Re-import
python3 -c "from openclaw_observability import init_tracer; print('OK')"
```

### "LLM calls not showing"

Make sure you're calling `tracer.add_llm_call()`:

```python
tracer = get_tracer()
tracer.add_llm_call(
    model="...",
    prompt="...",
    response="...",
    tokens={...},
    latency_ms=100,
)
```

---

## 📚 Next Steps

1. **Try LangChain example:** `python3 examples/langchain_example.py`
2. **Read full docs:** `README.md`
3. **Add to your agent:** Use `@observe` decorator
4. **Explore UI:** Click traces, inspect steps
5. **Share feedback:** What features do you need?

---

## 🎯 Common Use Cases

### Use Case 1: "Why did my agent fail?"
1. Open UI → find failed trace (🔴 red status)
2. Click trace → see execution graph
3. Click failed step → see error details
4. **Root cause:** "LLM timeout after 30s"

### Use Case 2: "Which step is slow?"
1. Open trace → see duration per step
2. Identify bottleneck: "Database lookup taking 5s"
3. Optimize or cache that step
4. Re-run → verify improvement

### Use Case 3: "How much am I spending?"
1. Open trace → see LLM calls
2. Check tokens + cost per call
3. Total cost shown in metadata
4. Optimize: "Switch 80% of calls to cheaper model"

---

## 🚀 You're Ready!

**Next command:**
```bash
python3 examples/basic_example.py && python3 server/app.py
```

**Then open:** http://localhost:5000

**Happy debugging!** 🎉

---

**Questions?** Read `README.md` or check `BUILD-REPORT.md`
