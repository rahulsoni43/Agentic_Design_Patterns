# AI Agent Patterns - Quick Reference Cheat Sheet

One-page reference for all 8 essential patterns.

---

## 1. Prompt Chaining 🔗

**What:** Break task into steps, pass output from step → step

**When:** Complex tasks needing multiple operations

**Code Pattern:**
```python
# Step 1
result1 = agent.call("Get all pods")

# Step 2 (uses result1)
result2 = agent.call(f"Analyze these pods: {result1}")

# Step 3 (uses result2)
result3 = agent.call(f"Suggest fixes for: {result2}")
```

**SRE Use Cases:**
- Diagnose → Analyze → Fix
- Collect → Correlate → Report
- Check → Validate → Deploy

---

## 2. Routing 🔀

**What:** Direct query to the right specialist agent

**When:** Multiple specialized agents available

**Code Pattern:**
```python
def route_query(query):
    if "pod" in query:
        return k8s_agent.handle(query)
    elif "log" in query:
        return log_agent.handle(query)
    else:
        return general_agent.handle(query)
```

**SRE Use Cases:**
- Route by service (K8s, DB, Network)
- Route by urgency (P0 → senior, P3 → junior)
- Route by type (incident vs question)

---

## 3. Parallelization ⚡

**What:** Run multiple tasks simultaneously

**When:** Independent tasks that can run concurrently

**Code Pattern:**
```python
import asyncio

async def collect_all():
    tasks = [
        check_pods(),
        check_nodes(),
        check_events()
    ]
    results = await asyncio.gather(*tasks)
    return results
```

**SRE Use Cases:**
- Check multiple clusters at once
- Collect from multiple data sources
- Run multiple health checks

---

## 4. Reflection 🪞

**What:** Agent reviews and improves its own output

**When:** High accuracy needed, or initial answer seems wrong

**Code Pattern:**
```python
# First attempt
answer = agent.analyze(problem)

# Reflection
if answer.confidence < 70:
    critique = agent.reflect(answer, problem)
    answer = agent.improve(answer, critique)

return answer
```

**SRE Use Cases:**
- Double-check before applying fix
- Verify diagnosis before escalating
- Review runbook before sharing

---

## 5. Tool Use 🛠️

**What:** Agent calls external tools/APIs/commands

**When:** Need to interact with real systems (not just chat)

**Code Pattern:**
```python
tools = [
    Tool(name="kubectl", func=run_kubectl),
    Tool(name="search_logs", func=grep_logs),
    Tool(name="restart_pod", func=kubectl_delete)
]

agent = Agent(tools=tools)

# Agent decides which tool to use
result = agent.run("Check if pod is healthy")
# Internally: agent calls kubectl tool
```

**SRE Use Cases:**
- Execute kubectl commands
- Query Prometheus
- Search logs
- Restart services

---

## 6. Multi-Agent 🤝

**What:** Multiple specialized agents collaborating

**When:** Complex problem needs different expertise

**Code Pattern:**
```python
class Orchestrator:
    def __init__(self):
        self.k8s_agent = K8sAgent()
        self.log_agent = LogAgent()
        self.db_agent = DBAgent()

    async def investigate(self, issue):
        # All agents work in parallel
        k8s_data = await self.k8s_agent.check()
        log_data = await self.log_agent.check()
        db_data = await self.db_agent.check()

        # Synthesize findings
        return self.synthesize(k8s_data, log_data, db_data)
```

**SRE Use Cases:**
- Infra + App + DB investigation
- Collection + Analysis + Reporting agents
- Monitoring + Alerting + Remediation

---

## 7. Memory 🧠

**What:** Remember past interactions/incidents

**When:** Want to learn from history

**Code Pattern:**
```python
class IncidentMemory:
    def save(self, incident):
        # Store in DB/file
        self.db.insert(incident)

    def recall(self, query):
        # Find similar past incidents
        return self.db.search_similar(query)

# Usage
memory = IncidentMemory()
similar = memory.recall("pod crashlooping")

if similar:
    return f"This happened before: {similar.solution}"
```

**SRE Use Cases:**
- "We fixed this before"
- Pattern recognition
- Runbook generation
- Historical analysis

---

## 8. Guardrails 🚧

**What:** Prevent dangerous/wrong actions

**When:** Agent has power to execute commands

**Code Pattern:**
```python
class SafetyGuard:
    DANGEROUS = ["delete", "drop", "rm"]
    PROTECTED = ["production", "prod"]

    def validate(self, command, namespace):
        # Check namespace
        if namespace in self.PROTECTED:
            # Check command
            if any(word in command for word in self.DANGEROUS):
                raise SecurityError("Cannot run in production")

        # Check requires confirmation
        if "scale" in command and "--replicas=0" in command:
            return "REQUIRES_APPROVAL"

        return "SAFE"
```

**SRE Use Cases:**
- Block prod deletions
- Require approval for scaling
- Prevent scaling to 0
- Audit all actions

---

## Quick Decision Tree

### "Which pattern should I use?"

```
Is task complex with multiple steps?
├─ YES → Use Prompt Chaining
└─ NO → Continue

Do I have specialized agents?
├─ YES → Use Routing
└─ NO → Continue

Can tasks run simultaneously?
├─ YES → Use Parallelization
└─ NO → Continue

Need to interact with real systems?
├─ YES → Use Tool Use (MOST IMPORTANT!)
└─ NO → Continue

Need high accuracy?
├─ YES → Use Reflection
└─ NO → Continue

Problem needs multiple expertise areas?
├─ YES → Use Multi-Agent
└─ NO → Continue

Want to learn from past?
├─ YES → Use Memory
└─ NO → Continue

Agent can break things?
├─ YES → Use Guardrails (CRITICAL!)
└─ NO → You're good!
```

---

## Common Combinations

### Incident Investigation Agent
```
✓ Tool Use (kubectl, logs)
✓ Prompt Chaining (collect → analyze → fix)
✓ Parallelization (check multiple things)
✓ Memory (recall similar incidents)
✓ Guardrails (don't break prod)
```

### Deployment Agent
```
✓ Tool Use (kubectl apply)
✓ Prompt Chaining (deploy → verify → rollback if needed)
✓ Reflection (double-check before deploy)
✓ Guardrails (safety checks)
```

### Monitoring Agent
```
✓ Multi-Agent (K8s + Logs + Metrics)
✓ Parallelization (check all at once)
✓ Memory (compare to baseline)
✓ Routing (send to right team)
```

---

## Performance Impact

| Pattern | Speed Impact | Cost Impact | Complexity |
|---------|-------------|-------------|------------|
| Chaining | Slower (sequential) | Higher (multiple calls) | Low |
| Routing | Faster (skip unnecessary) | Lower (only needed agents) | Medium |
| Parallelization | Much Faster | Same | Low |
| Reflection | Slower (extra calls) | Higher | Medium |
| Tool Use | Variable | Low (external calls) | Medium |
| Multi-Agent | Variable | Higher | High |
| Memory | Faster (skip work) | Lower (reuse) | Medium |
| Guardrails | Negligible | Negligible | Low |

---

## Anti-Patterns (Don't Do This!)

❌ **Infinite Loops**
```python
# BAD: Agent keeps reflecting forever
while confidence < 100:
    answer = reflect(answer)  # Never stops!
```
✅ Fix: Limit iterations
```python
for i in range(3):  # Max 3 attempts
    if confidence > 80:
        break
    answer = reflect(answer)
```

❌ **No Guardrails on Production**
```python
# BAD: Agent can do anything
agent.execute(user_command)
```
✅ Fix: Add safety checks
```python
if is_dangerous(command) and is_production(env):
    raise SecurityError()
```

❌ **Sequential When Parallel Possible**
```python
# BAD: Takes 30 seconds
pods = check_pods()      # 10s
nodes = check_nodes()    # 10s
events = check_events()  # 10s
```
✅ Fix: Run in parallel
```python
# GOOD: Takes 10 seconds
results = await asyncio.gather(
    check_pods(),
    check_nodes(),
    check_events()
)
```

❌ **Forgetting Error Handling**
```python
# BAD: Crashes on API error
result = api.call()
```
✅ Fix: Handle errors gracefully
```python
try:
    result = api.call()
except APIError as e:
    logger.error(f"API failed: {e}")
    result = fallback_value
```

---

## File Locations (In This Repo)

| Pattern | Notebook File |
|---------|--------------|
| Chaining | `notebooks/Chapter 1_ Prompt Chaining (Code Example)` |
| Routing | `notebooks/Chapter 2_ Routing (Google ADK Code Example)` |
| Parallelization | `notebooks/Chapter 3_ Parallelization (Google ADK Code Example).ipynb` |
| Reflection | `notebooks/Chapter 4_ Reflection (Iterative Loop reflection)` |
| Tool Use | `notebooks/Chapter 5_ Tool Use (LangChain Code Example)` |
| Multi-Agent | `notebooks/Chapter 7_ Multi-Agent Collaboration - Code Example (ADK + Gemini Parallel).ipynb` |
| Memory | `notebooks/Chapter 8_ Memory Management - Code Example (LangChain and LangGraph)` |
| Guardrails | `notebooks/Chapter 18_ Guardrails_Safety Patterns (Practical Code Examples for Guardrails)` |

---

## Real Examples in Sherlock

| Pattern | Where Used in Sherlock |
|---------|------------------------|
| Chaining | `src/investigator.py` - collect → correlate → analyze |
| Parallelization | `src/investigator.py` - `_collect_data()` uses asyncio.gather |
| Tool Use | `src/collectors/k8s_collector.py` - calls Kubernetes API |
| Memory | Phase 3 (not yet implemented) |
| Guardrails | `src/config.py` - `ENABLE_AUTO_REMEDIATION = False` |
| Multi-Agent | Phase 2 (planned with log + metrics agents) |

---

## Quick Tips

💡 **Start Simple**: One pattern at a time
💡 **Test Small**: Use dev cluster first
💡 **Measure Impact**: Track speed & accuracy
💡 **Safety First**: Always add guardrails
💡 **Iterate**: Ship, learn, improve

---

## Most Important for SRE

### TOP 3 Must-Know:
1. **Tool Use** - Agents that DO things (not just chat)
2. **Guardrails** - Don't break production
3. **Parallelization** - Speed = reduced MTTR

### Nice to Have:
4. Prompt Chaining
5. Memory
6. Multi-Agent

### Advanced:
7. Routing
8. Reflection

---

**Print this and keep it handy!** 📄
