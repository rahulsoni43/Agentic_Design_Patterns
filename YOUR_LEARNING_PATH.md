# Your AI Agent Learning Path 🚀

**Personalized for:** SRE/DevOps Engineer (15+ years IT, 8+ years SRE)
**Goal:** Master AI Agents for Infrastructure/Troubleshooting
**Timeline:** 4-6 weeks (1-2 hours/day)
**Approach:** Learn by DOING, not reading

---

## Why This Matters for You

As an SRE, you waste time on:
- ❌ Repeating same kubectl commands
- ❌ Searching logs manually
- ❌ Forgetting what you did last time
- ❌ Context switching between 10 tools

**AI Agents can:**
- ✅ Automate repetitive investigations
- ✅ Remember past incidents
- ✅ Correlate data from multiple sources
- ✅ Suggest fixes based on patterns

**You've already built Sherlock** - now let's understand the patterns behind it so you can build ANYTHING.

---

## The 8 Essential Patterns (For SRE/DevOps)

I've filtered the 21 chapters down to the **8 most useful for your work**. Skip the academic stuff.

### Week 1: Foundation (Patterns 1-3)
**Goal:** Understand how AI agents think and act

### Week 2: Power-Ups (Patterns 4-5)
**Goal:** Make agents smarter and more reliable

### Week 3: Advanced (Patterns 6-7)
**Goal:** Multi-agent systems and memory

### Week 4: Production (Pattern 8 + Project)
**Goal:** Deploy safely and monitor

---

## Week 1: Foundation

### 📘 Pattern 1: Prompt Chaining (Day 1-2)

**What it is:** Breaking complex tasks into steps, passing output from step 1 → step 2 → step 3

**SRE Example:**
```
Step 1: "Get all crashlooping pods" → [list of pods]
Step 2: "For each pod, get logs" → [logs]
Step 3: "Analyze logs for errors" → [root cause]
```

**Where you've seen it:** In Sherlock's investigator.py
```python
# Step 1: Collect data
events = await self._collect_data(query)

# Step 2: Correlate (uses output from step 1)
correlations = self.correlator.correlate(events)

# Step 3: Analyze (uses output from step 2)
analysis = await self.root_cause_analyzer.analyze(query, events, correlations)
```

**Hands-on Exercise:**
```bash
cd notebooks/
# Open: Chapter 1_ Prompt Chaining (Code Example)
# Run it and understand how output flows

# Then modify it:
# Task: Create a 3-step chain for "Check pod health"
# Step 1: List pods
# Step 2: Filter unhealthy
# Step 3: Get details
```

**Why it matters:** Most AI agent tasks need multiple steps. Master this first.

---

### 📘 Pattern 2: Routing (Day 3-4)

**What it is:** AI decides which specialist to send the task to (like a router)

**SRE Example:**
```
User: "API is slow"

Router decides:
- If metrics issue → Send to Prometheus Agent
- If log issue → Send to Log Analyzer Agent
- If K8s issue → Send to K8s Agent
```

**Where you've seen it:** Sherlock's investigator decides which collectors to use

**Future enhancement for Sherlock:**
```python
# Add routing logic
if "logs" in query.lower():
    use_log_collector = True
elif "metrics" in query.lower():
    use_metrics_collector = True
else:
    use_all_collectors = True
```

**Hands-on Exercise:**
```bash
# Open: Chapter 2_ Routing (Google ADK Code Example)
# Run the example

# Then build:
# Task: Create a router for SRE queries
# Routes:
# - "pod", "container", "k8s" → K8s Agent
# - "slow", "latency", "timeout" → Performance Agent
# - "error", "crash", "5xx" → Log Agent
```

**Why it matters:** Don't waste time/money calling every agent. Route efficiently.

---

### 📘 Pattern 3: Parallelization (Day 5-6)

**What it is:** Run multiple tasks at the same time (async)

**SRE Example:**
```
Instead of:
1. Check pods (10 sec)
2. Check nodes (10 sec)
3. Check events (10 sec)
Total: 30 seconds

Do parallel:
1. Check pods      }
2. Check nodes     } All at once
3. Check events    }
Total: 10 seconds
```

**Where you've seen it:** In Sherlock's data collection!
```python
# sherlock-sre/src/investigator.py
async def _collect_data(self, query: str) -> List[Event]:
    tasks = []
    for collector in self.collectors:
        tasks.append(collector.collect(query))

    # All collectors run in parallel!
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Hands-on Exercise:**
```bash
# Open: Chapter 3_ Parallelization (Google ADK Code Example).ipynb

# Then test performance:
# Task: Compare sequential vs parallel
# Collect data from 3 namespaces
# Time both approaches
# See the difference!
```

**Why it matters:** Speed = MTTR reduction = hero status

---

### 🎯 Week 1 Project: Upgrade Sherlock

**Task:** Add routing to Sherlock

Currently, Sherlock always collects everything. Make it smart:

```python
# Add to sherlock-sre/src/investigator.py
def _route_query(self, query: str) -> List[str]:
    """Decide which collectors to use based on query"""

    collectors_to_use = []

    query_lower = query.lower()

    # Route based on keywords
    if any(word in query_lower for word in ["pod", "container", "k8s"]):
        collectors_to_use.append("k8s_collector")

    if any(word in query_lower for word in ["log", "error", "crash"]):
        collectors_to_use.append("log_collector")  # Phase 2

    if any(word in query_lower for word in ["slow", "latency", "cpu", "memory"]):
        collectors_to_use.append("metrics_collector")  # Phase 2

    # If no specific route, use all
    if not collectors_to_use:
        collectors_to_use = ["k8s_collector"]

    return collectors_to_use
```

**Test it:**
```bash
python -m src.cli investigate "pod is crashlooping"  # Should use K8s only
python -m src.cli investigate "check everything"     # Should use all
```

---

## Week 2: Power-Ups

### 📘 Pattern 4: Reflection (Day 7-8)

**What it is:** Agent reviews its own answer and improves it (self-critique)

**SRE Example:**
```
Agent's first answer: "Pod crashed due to OOM"

Reflection: "Wait, let me verify...
- Is memory limit set? Yes
- Is it too low? Let me check similar pods...
- Actually, sidecar has no limit! That's the real issue"

Improved answer: "Main container fine. Sidecar has no memory limit."
```

**Where it could go in Sherlock:**
```python
# After getting root cause
if analysis.confidence < 70:
    # Re-analyze with more context
    analysis = await self._reflect_and_improve(analysis, events)
```

**Hands-on Exercise:**
```bash
# Open: Chapter 4_ Reflection (Iterative Loop reflection)

# Then build:
# Task: Add reflection to a kubectl diagnosis
# 1. Get initial diagnosis
# 2. Agent asks: "Did I check everything?"
# 3. Re-run with missed checks
# 4. Compare answers
```

**Why it matters:** Reduces wrong diagnoses. Better than humans at self-checking.

---

### 📘 Pattern 5: Tool Use (Day 9-11)

**What it is:** Agent can call external tools/APIs/commands (not just chat)

**SRE Example:**
```
User: "Check if pod is healthy"

Agent thinks: "I need kubectl command"
Agent calls: execute_command("kubectl get pod api-gateway -n prod")
Agent gets: Output
Agent responds: "Pod is CrashLooping. Exit code 137."
```

**Where you've seen it:** This is CORE to Sherlock
```python
# Sherlock's tools:
- kubernetes.client (calls K8s API)
- anthropic.Client (calls Claude API)
- asyncio (parallel execution)
```

**Hands-on Exercise:**
```bash
# Open: Chapter 5_ Tool Use (LangChain Code Example)

# Then build:
# Task: Create an SRE agent with these tools:
# - kubectl_tool(command) → runs kubectl
# - search_logs_tool(pattern) → greps logs
# - restart_pod_tool(pod_name) → restarts pod

# Agent should decide WHICH tool to use based on question
```

**Why it matters:** This is what separates chatbots from AGENTS. Agents DO things.

---

### 🎯 Week 2 Project: Add Tools to Sherlock

**Task:** Add actionable commands to Sherlock

Currently, Sherlock suggests commands. Make it execute them (with approval):

```python
# Add to sherlock-sre/src/interfaces/slack_bot.py

async def handle_action_button(self, action, say):
    """User clicked 'Execute' button"""

    command = action['value']  # e.g., "kubectl delete pod xyz"

    # Safety check
    if "delete" in command or "scale" in command:
        await say(f"⚠️ Dangerous command requires confirmation:\n`{command}`\n\nReply 'CONFIRM' to execute")
        return

    # Execute safe commands
    result = await execute_kubectl(command)
    await say(f"✅ Executed: `{command}`\n\nOutput:\n```{result}```")
```

**Test it:**
```bash
@sherlock investigate crashloop
# Sherlock responds with buttons: [View Logs] [Restart Pod] [Show More]
# You click [View Logs] → Auto-executes kubectl logs
```

---

## Week 3: Advanced

### 📘 Pattern 6: Multi-Agent Collaboration (Day 12-14)

**What it is:** Multiple specialized agents working together

**SRE Example:**
```
Coordinator Agent
├─ K8s Agent (checks pods, nodes)
├─ Log Agent (checks logs)
├─ Metrics Agent (checks Prometheus)
├─ History Agent (checks past incidents)
└─ Summarizer Agent (combines all findings)
```

**Where you could use it:**
```python
# Sherlock Phase 2 architecture
class InvestigationOrchestrator:
    def __init__(self):
        self.k8s_agent = K8sAgent()
        self.log_agent = LogAgent()
        self.metrics_agent = MetricsAgent()
        self.historian_agent = HistorianAgent()

    async def investigate(self, query):
        # All agents work in parallel
        k8s_findings = await self.k8s_agent.investigate(query)
        log_findings = await self.log_agent.investigate(query)
        metrics_findings = await self.metrics_agent.investigate(query)
        history_findings = await self.historian_agent.find_similar(query)

        # Combine with AI
        return await self._synthesize(k8s_findings, log_findings, ...)
```

**Hands-on Exercise:**
```bash
# Open: Chapter 7_ Multi-Agent Collaboration - Code Example (ADK + Gemini Parallel).ipynb

# Then build:
# Task: Create a mini multi-agent system
# Agents:
# 1. DiagnosticAgent - checks current state
# 2. HistoryAgent - checks similar past issues
# 3. SolutionAgent - suggests fixes
# Coordinator combines all 3
```

**Why it matters:** Complex problems need specialized expertise.

---

### 📘 Pattern 7: Memory Management (Day 15-16)

**What it is:** Agent remembers past conversations/incidents

**SRE Example:**
```
Week 1:
User: "API slow due to memory leak"
Agent: [Investigates, finds fix]

Week 2:
User: "API slow again"
Agent: "Last time this was a memory leak in auth-service. Checking..."
Agent: [Skips investigation, goes straight to known fix]
```

**Where Sherlock needs it:**
```python
# Add to Sherlock Phase 3
class IncidentMemory:
    def store_incident(self, investigation: Investigation):
        """Save to vector DB for similarity search"""

    def find_similar(self, query: str) -> List[PastIncident]:
        """Find similar past incidents"""
```

**Hands-on Exercise:**
```bash
# Open: Chapter 8_ Memory Management - Code Example (LangChain and LangGraph)

# Then build:
# Task: Create incident memory
# 1. Save investigation results to JSON
# 2. When new issue comes, search past JSON files
# 3. If similar (>80% match), suggest past solution
```

**Why it matters:** Stop solving the same problem twice.

---

### 📘 Pattern 8: Guardrails & Safety (Day 17-18)

**What it is:** Prevent agent from doing dangerous things

**SRE Example:**
```
User: "Delete all pods in production"

Without guardrails:
Agent: *deletes everything* 💥

With guardrails:
Agent: "⚠️ This is a destructive operation affecting PRODUCTION.
        Requires manual approval. Will not execute."
```

**Where Sherlock needs it:**
```python
# Add to sherlock-sre/src/config.py
ENABLE_AUTO_REMEDIATION = False  # Already there!

# Add safety checks
class SafetyGuard:
    DANGEROUS_KEYWORDS = ["delete", "rm", "drop", "truncate"]
    PROTECTED_NAMESPACES = ["production", "prod"]

    def validate_command(self, command: str, namespace: str):
        if namespace in self.PROTECTED_NAMESPACES:
            if any(word in command for word in self.DANGEROUS_KEYWORDS):
                raise SecurityError("Cannot run destructive command in production")
```

**Hands-on Exercise:**
```bash
# Open: Chapter 18_ Guardrails_Safety Patterns (Practical Code Examples for Guardrails)

# Then build:
# Task: Add guardrails to Sherlock
# Rules:
# 1. Never delete pods in production without confirmation
# 2. Never scale to 0 replicas
# 3. Warn if changing resource limits by >50%
# 4. Log all executed commands to audit trail
```

**Why it matters:** Don't get fired. Safety first.

---

### 🎯 Week 3 Project: Sherlock with Memory

**Task:** Make Sherlock remember past incidents

```python
# Add new file: sherlock-sre/src/storage/incident_memory.py

import json
from datetime import datetime
from pathlib import Path

class IncidentMemory:
    def __init__(self, storage_path="./incidents/"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

    def save_incident(self, investigation):
        """Save incident for future reference"""
        incident_data = {
            "timestamp": datetime.now().isoformat(),
            "query": investigation.query,
            "root_cause": investigation.analysis.root_cause,
            "events_summary": [e.message for e in investigation.events[:5]],
            "solution": investigation.recommended_actions[0].command
        }

        filename = f"incident_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(self.storage_path / filename, 'w') as f:
            json.dump(incident_data, f, indent=2)

    def find_similar(self, query: str, threshold=0.7) -> List[dict]:
        """Find similar past incidents"""
        # Simple keyword matching (Phase 3 will use vector similarity)
        similar = []
        for file in self.storage_path.glob("*.json"):
            with open(file) as f:
                incident = json.load(f)

                # Simple similarity: count common words
                query_words = set(query.lower().split())
                incident_words = set(incident['query'].lower().split())
                similarity = len(query_words & incident_words) / len(query_words | incident_words)

                if similarity > threshold:
                    similar.append(incident)

        return similar
```

**Test it:**
```bash
# First investigation
python -m src.cli investigate "pod crashlooping due to memory"
# Sherlock saves incident

# Later investigation (similar)
python -m src.cli investigate "pod crash memory issue"
# Sherlock finds similar incident and suggests same solution
```

---

## Week 4: Production Ready

### Day 19-20: Evaluation & Monitoring

**Pattern:** How to know if your agent is working well

**Metrics to track:**
```python
# Add to Sherlock
class AgentMetrics:
    investigations_total = 0
    investigations_successful = 0
    average_response_time = 0
    user_feedback_positive = 0

    def track_investigation(self, investigation):
        self.investigations_total += 1
        if investigation.analysis.confidence > 70:
            self.investigations_successful += 1
```

**Hands-on:**
```bash
# Open: Chapter 19_ Evaluation and Monitoring (LLM as a Judge)

# Build: Add metrics dashboard to Sherlock
# Track:
# - How many investigations per day?
# - Average confidence score
# - Which types of issues most common?
# - Response time trends
```

---

### Day 21: Final Project - Your Own Agent

**Choose ONE project that solves YOUR real problem:**

#### Option 1: Incident Response Bot
```
Agent that:
1. Monitors Slack for keywords ("down", "slow", "error")
2. Automatically starts investigation
3. Posts findings to incident channel
4. Updates incident ticket
5. Suggests on-call person if can't auto-fix
```

#### Option 2: Deployment Safety Bot
```
Agent that:
1. Watches for new K8s deployments
2. Checks if deployment is healthy (5 min after deploy)
3. Runs smoke tests
4. If failing: Auto-rollback
5. Posts results to Slack
```

#### Option 3: Cost Optimization Agent
```
Agent that:
1. Scans all pods daily
2. Finds over-provisioned resources
3. Finds unused PVCs
4. Calculates waste
5. Suggests optimizations
6. Creates PRs to reduce resource requests
```

#### Option 4: Runbook Generator
```
Agent that:
1. After each investigation, extracts pattern
2. Builds a runbook (if X happens, do Y)
3. Stores in knowledge base
4. Next time: Suggests runbook instead of investigating
```

**Requirements:**
- Must use at least 3 patterns you learned
- Must be production-safe (guardrails!)
- Must be deployed (Docker or K8s)
- Must have basic metrics
- Solve a real problem for you

---

## Beyond the Basics (Optional Advanced Topics)

If you finish early or want more:

### 🔥 RAG (Retrieval-Augmented Generation)
**Use case:** Search through 1000s of past incidents
**File:** Chapter 14_ Knowledge Retrieval (RAG LangChain)

### 🔥 Planning
**Use case:** Agent creates multi-step plan before executing
**File:** Chapter 6_ Planning - Code Example

### 🔥 Reasoning Techniques (Chain-of-Thought)
**Use case:** Make agent explain its reasoning
**File:** Chapter 17_ Reasoning Techniques (Prompt with CoT for Agent)

### 🔥 Human-in-the-Loop
**Use case:** Agent asks for approval before risky actions
**File:** Chapter 13_ Human-in-the-Loop (Customer Support Agent)

---

## Your Learning Workflow (Daily)

### Every Day:
```bash
1. Read pattern explanation (10 min) ← This file
2. Open corresponding notebook (20 min)
3. Run the example code
4. Understand what it does
5. Modify it for your use case (30 min)
6. Apply it to Sherlock or build new tool
7. Test it on real cluster
```

### Every Week:
```bash
1. Complete the weekly project
2. Deploy it
3. Use it for 1 week
4. Iterate based on what works/doesn't
```

---

## How to Use the Notebooks

### Step 1: Set up Jupyter
```bash
cd /home/user/Agentic_Design_Patterns

# Install Jupyter
pip install jupyter notebook

# Start notebook server
jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser
```

### Step 2: Open notebooks
```bash
# In browser, go to: http://localhost:8888
# Navigate to: notebooks/
# Click on: Chapter 1_ Prompt Chaining (Code Example)
```

### Step 3: Run cells
```
- Click each cell
- Press Shift+Enter to run
- Read the output
- Modify the code
- Run again
```

### Step 4: Copy patterns to your code
```bash
# Found something useful?
# Copy pattern to Sherlock or new project
# Adapt it to your needs
```

---

## Key Resources

### Quick Reference
```bash
# All notebooks
cd /home/user/Agentic_Design_Patterns/notebooks/

# Your projects
cd /home/user/Agentic_Design_Patterns/sherlock-sre/
cd /home/user/Agentic_Design_Patterns/my_work_agents/

# This learning guide
/home/user/Agentic_Design_Patterns/YOUR_LEARNING_PATH.md
```

### Important Patterns (Priority Order)
1. **Tool Use** - Agents that DO things (most important!)
2. **Prompt Chaining** - Multi-step reasoning
3. **Parallelization** - Speed matters
4. **Guardrails** - Don't break production
5. **Memory** - Learn from past
6. **Multi-Agent** - Complex workflows
7. **Reflection** - Self-improvement
8. **Routing** - Efficiency

---

## Success Metrics

After 4 weeks, you should be able to:

✅ Explain how AI agents work to your team
✅ Build a custom agent for any SRE task
✅ Understand tradeoffs (speed vs accuracy, cost vs quality)
✅ Deploy agents safely to production
✅ Debug when agents fail
✅ Improve Sherlock with new capabilities
✅ Build your own startup idea (maybe!)

---

## Getting Help

### Stuck on a concept?
```bash
# Ask me! I'll explain it better
# Or: Check the notebook - it has detailed comments
# Or: Run the code and see what breaks
```

### Need a real example?
```bash
# Look at Sherlock - you already built it!
# Find pattern in: sherlock-sre/src/
# See how it's used
```

### Want to go deeper?
```bash
# Then (and only then) read the PDF
# But focus on chapters relevant to what you're building
```

---

## The Secret

**You don't need to understand everything.**

You need to understand:
1. The pattern (what it does)
2. When to use it (your use case)
3. How to implement it (copy from examples)

That's it.

**Stop reading. Start building.**

The best way to learn is to build something you'll actually use.

You've already started with Sherlock - now make it better using these patterns!

---

## Next Steps

1. **Start tomorrow with Day 1 (Prompt Chaining)**
2. **Set up Jupyter**:
   ```bash
   pip install jupyter
   jupyter notebook
   ```
3. **Open first notebook**: `Chapter 1_ Prompt Chaining (Code Example)`
4. **Run every cell and understand what it does**
5. **Come back here for Day 2**

---

**Remember:** You're not trying to become a researcher. You're becoming an SRE who uses AI to solve problems 10x faster.

Let's go! 🚀
