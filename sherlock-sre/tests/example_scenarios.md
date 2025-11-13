# Sherlock SRE - Example Test Scenarios

This document provides example scenarios you can use to test Sherlock's investigation capabilities.

---

## Scenario 1: CrashLoopBackOff Investigation

**Description:** A pod is repeatedly crashing and restarting.

**Test Command:**
```bash
python -m src.cli investigate "Why is my pod in CrashLoopBackOff?"
```

**Expected Behavior:**
- Sherlock collects pod status events
- Identifies pods with high restart counts
- Checks container exit codes
- Looks for OOMKilled events
- Provides root cause analysis (e.g., memory limits too low, application bug)
- Suggests remediation actions (e.g., increase memory limits, check logs)

**Example Slack Command:**
```
@sherlock investigate my nginx-pod is crashlooping in production namespace
```

---

## Scenario 2: Node Issues

**Description:** A node is showing NotReady status or under pressure.

**Test Command:**
```bash
python -m src.cli investigate "Node is showing NotReady status"
```

**Expected Behavior:**
- Collects node status information
- Checks for resource pressure (disk, memory, PID)
- Identifies pods scheduled on the problematic node
- Correlates node issues with pod failures
- Suggests node drain/restart or resource cleanup

**Example Slack Command:**
```
@sherlock help my node ip-10-0-1-234 is not ready
```

---

## Scenario 3: High Memory Usage

**Description:** Investigating memory-related issues.

**Test Command:**
```bash
python -m src.cli investigate "Pod is using too much memory"
```

**Expected Behavior:**
- Finds pods with high memory usage
- Checks memory limits and requests
- Looks for OOMKilled events
- Identifies memory leak patterns
- Recommends memory limit adjustments or application profiling

**Example Slack Command:**
```
@sherlock my application is getting OOMKilled
```

---

## Scenario 4: API Latency

**Description:** Application is slow or returning errors.

**Test Command:**
```bash
python -m src.cli investigate "API is slow and returning 502 errors"
```

**Expected Behavior:**
- Checks for pod health issues
- Looks for resource constraints (CPU throttling)
- Checks for networking issues
- Correlates with recent deployments
- Suggests scaling, resource adjustments, or rollback

**Example Slack Command:**
```
@sherlock investigate API latency is high in production
```

---

## Scenario 5: Recent Deployment Issues

**Description:** Issues started after a deployment.

**Test Command:**
```bash
python -m src.cli investigate "Application failing after recent deployment"
```

**Expected Behavior:**
- Identifies recent deployments/rollouts
- Checks for image pull errors
- Looks for configuration issues
- Correlates deployment timing with failures
- Suggests rollback if appropriate

**Example Slack Command:**
```
@sherlock my latest deployment is causing errors
```

---

## Scenario 6: Cluster Health Check

**Description:** General cluster health overview.

**Test Command:**
```bash
python -m src.cli health
```

**Expected Behavior:**
- Shows overall cluster status
- Lists unhealthy nodes
- Lists crashlooping pods
- Shows recent critical events
- Provides summary of issues

**Example Slack Command:**
```
@sherlock what's the current cluster health?
```

---

## Scenario 7: Namespace-Specific Issues

**Description:** Investigating issues in a specific namespace.

**Test Command:**
```bash
python -m src.cli investigate "Issues in production namespace"
```

**Expected Behavior:**
- Focuses on events from specified namespace
- Provides namespace-specific analysis
- Lists all problematic resources in that namespace

**Example Slack Command:**
```
@sherlock check production namespace for issues
```

---

## Scenario 8: Resource Quotas

**Description:** Pods not scheduling due to resource constraints.

**Test Command:**
```bash
python -m src.cli investigate "Pods not scheduling"
```

**Expected Behavior:**
- Checks for pending pods
- Identifies resource quota issues
- Looks for node selector mismatches
- Checks for insufficient cluster resources
- Suggests increasing quotas or adding nodes

**Example Slack Command:**
```
@sherlock why are my pods stuck in pending?
```

---

## Scenario 9: Persistent Volume Issues

**Description:** Storage-related problems.

**Test Command:**
```bash
python -m src.cli investigate "PVC not binding"
```

**Expected Behavior:**
- Checks PVC status
- Looks for storage class issues
- Identifies capacity problems
- Suggests resolution steps

**Example Slack Command:**
```
@sherlock my persistent volume claim won't bind
```

---

## Scenario 10: Multi-Event Correlation

**Description:** Complex issue with multiple correlated events.

**Test Command:**
```bash
python -m src.cli investigate "Multiple pods failing across different namespaces"
```

**Expected Behavior:**
- Collects events from multiple namespaces
- Identifies common root causes (e.g., node failure, network issue)
- Correlates seemingly unrelated failures
- Provides comprehensive analysis of cascading failures

**Example Slack Command:**
```
@sherlock everything is broken, help!
```

---

## Interactive Testing in Slack

Once your Slack bot is running, try these conversational commands:

```
# Get help
@sherlock help

# Ask general questions
@sherlock what's wrong with my cluster?

# Be specific
@sherlock investigate my api-gateway pod in production is crashlooping

# Check health
@sherlock show cluster health

# Follow up questions
@sherlock why is it happening?
@sherlock what should I do?
```

---

## Expected Output Format

For each investigation, Sherlock should provide:

1. **Summary**
   - One-line summary of the issue

2. **Evidence**
   - List of relevant events
   - Timestamps and sources
   - Severity levels

3. **Correlations**
   - Related events
   - Temporal relationships
   - Causal relationships

4. **Root Cause Analysis**
   - Primary root cause
   - Contributing factors
   - Confidence level (0-100%)
   - AI reasoning

5. **Recommended Actions**
   - Prioritized list of actions
   - kubectl commands (ready to copy-paste)
   - Safety warnings if applicable

---

## Creating Your Own Test Scenarios

To test with your actual cluster:

1. **Identify a real issue** you've experienced
2. **Formulate it as a question** (natural language)
3. **Run investigation:**
   ```bash
   python -m src.cli investigate "your question here"
   ```
4. **Review the output:**
   - Is the root cause correct?
   - Are the recommendations helpful?
   - Would this have saved you time?

---

## Performance Testing

Test Sherlock's performance:

```bash
# Time an investigation
time python -m src.cli investigate "test issue"

# Should complete in:
# - Data collection: 5-15 seconds
# - AI analysis: 3-10 seconds
# - Total: < 30 seconds
```

---

## Debugging Tests

If a test fails, use verbose logging:

```bash
LOG_LEVEL=DEBUG python -m src.cli investigate "test issue"
```

Or use the diagnostics command:

```bash
python -m src.cli diagnostics
```

---

## Automated Testing

For CI/CD integration:

```bash
# Run verification tests
python tests/test_verification.py

# Check exit code
echo $?  # 0 = success, 1 = failure
```

---

## Next Steps

1. Run through these scenarios
2. Compare Sherlock's analysis to your own troubleshooting
3. Refine your questions based on what works best
4. Share successful investigation patterns with your team
5. Build up a knowledge base of effective queries

---

**Happy investigating!** 🔍
