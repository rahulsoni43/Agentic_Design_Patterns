# Getting Started with Your Work AI Agents

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
cd /home/user/Agentic_Design_Patterns/my_work_agents

# Install required packages
pip install -r requirements.txt
```

### 2. Get Your Claude API Key

1. Go to: https://console.anthropic.com/
2. Sign up / Log in
3. Go to "API Keys" section
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-...`)

### 3. Set Your API Key

```bash
# Set for current session
export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"

# Or add to your ~/.bashrc or ~/.zshrc for persistence
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Test It Works

```bash
# Try the simple example first
python examples/01_simple_log_analyzer.py

# If that works, you're ready!
```

---

## Usage Examples

### Log Analysis

```bash
# Analyze nginx error logs
python agents/log_analyzer.py --file /var/log/nginx/error.log

# Analyze last 500 lines
python agents/log_analyzer.py --file /var/log/syslog --lines 500

# Using the unified CLI
./work-agent logs analyze /var/log/nginx/error.log
```

### Config Review

```bash
# Review nginx config
python agents/config_reviewer.py /etc/nginx/nginx.conf

# Review kubernetes manifest
python agents/config_reviewer.py deployment.yaml

# Using the unified CLI
./work-agent config review nginx.conf
```

### Incident Response

```bash
# Get help during an incident
python agents/incident_helper.py "API is returning 502 errors"

# With additional context
python agents/incident_helper.py "High memory usage" --context "Started after deployment"

# Using the unified CLI
./work-agent incident diagnose "Database connection timeouts"
```

### Quick Questions

```bash
# Explain a command
./work-agent explain "awk '{print \$1}' | sort | uniq -c"

# Ask any DevOps question
./work-agent ask "how do I check kubernetes pod logs for errors?"

# Infrastructure questions
./work-agent ask "what's the best way to optimize nginx for high traffic?"
```

---

## Learning Path

### Week 1: Basics

**Day 1-2: Run the examples**
```bash
# Start with the simplest example
python examples/01_simple_log_analyzer.py

# Then try prompt chaining
python examples/02_log_analyzer_with_chaining.py
```

**Day 3-4: Use on real files**
```bash
# Analyze your actual logs
python agents/log_analyzer.py --file /var/log/syslog

# Review your actual configs
python agents/config_reviewer.py /etc/nginx/nginx.conf
```

**Day 5-7: Customize for your needs**
- Edit the prompts in the agents
- Add new analysis steps
- Integrate with your tools (Slack, PagerDuty, etc.)

### Week 2: Build Your Own

**Study the patterns:**
1. Open `agents/log_analyzer.py`
2. See how it uses:
   - Prompt Chaining (multiple steps)
   - Tool Use (reading files)
   - Reflection (self-review)
   - Guardrails (safety checks)

**Create your own agent:**
```python
# Copy the template structure
# Modify the prompts for your specific use case
# Examples:
# - Database query optimizer
# - Security audit agent
# - Cost analysis agent
# - Documentation generator
```

---

## Integration with Your Workflow

### Add to PATH

```bash
# Add work-agent to your PATH
sudo ln -s /home/user/Agentic_Design_Patterns/my_work_agents/work-agent /usr/local/bin/work-agent

# Now use from anywhere
work-agent logs analyze /var/log/nginx/error.log
```

### Shell Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Quick aliases
alias analyze-logs='work-agent logs analyze'
alias review-config='work-agent config review'
alias incident='work-agent incident diagnose'
alias explain='work-agent explain'

# Usage:
# analyze-logs /var/log/syslog
# review-config nginx.conf
# incident "API is down"
# explain "kubectl get pods"
```

### Integrate with Your Tools

**Example: Auto-analyze logs on error**
```bash
#!/bin/bash
# hooks/on-error.sh

# When error detected, auto-analyze
if grep -q "ERROR" /var/log/app.log; then
    work-agent logs analyze /var/log/app.log > /tmp/analysis.txt
    # Send to Slack, email, etc.
fi
```

**Example: Pre-deployment config check**
```bash
#!/bin/bash
# hooks/pre-deploy.sh

# Review config before deploying
work-agent config review nginx.conf
read -p "Proceed with deployment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl apply -f deployment.yaml
fi
```

---

## Understanding the Code

### Simple Example (01_simple_log_analyzer.py)
- **Lines 1-20:** Import and setup
- **Lines 22-45:** One function that calls Claude
- **Lines 47-80:** Example usage

**Key takeaway:** It's just an API call! Very simple.

### Advanced Example (agents/log_analyzer.py)
- **Lines 1-30:** Class structure
- **Lines 32-60:** Tool: Read file with safety checks (Guardrails)
- **Lines 62-95:** Step 1: Extract errors (Prompt Chaining)
- **Lines 97-130:** Step 2: Categorize (Prompt Chaining)
- **Lines 132-175:** Step 3: Action plan (Prompt Chaining)
- **Lines 177-200:** Step 4: Self-review (Reflection)
- **Lines 202-250:** Main pipeline that chains everything

**Key takeaway:** Complex agents are just multiple simple calls chained together!

---

## Cost Management

**Typical usage costs:**
- Simple question: $0.01 - $0.05
- Log analysis: $0.10 - $0.50
- Full incident analysis: $0.50 - $2.00

**Monthly estimates:**
- Light use (5-10 queries/day): $5-15/month
- Medium use (20-30 queries/day): $20-40/month
- Heavy use (50+ queries/day): $50-100/month

**Tips to reduce costs:**
- Limit log file size (use --lines parameter)
- Use cheaper models for simple tasks (claude-haiku)
- Cache results for repeated queries
- Set budget alerts in Anthropic console

---

## Next Steps

### Customize for Your Stack

Edit the prompts to include your specific:
- Tech stack (AWS, GCP, Kubernetes, etc.)
- Naming conventions
- Internal tools and commands
- Company-specific procedures

### Build New Agents

Ideas based on your SRE/DevOps work:
1. **Performance Analyzer** - Analyze metrics, suggest optimizations
2. **Security Auditor** - Check for vulnerabilities
3. **Cost Optimizer** - Find ways to reduce cloud spend
4. **Documentation Generator** - Auto-generate runbooks
5. **Capacity Planner** - Predict resource needs
6. **On-Call Assistant** - Help with on-call rotations

### Learn More Patterns

Study the notebooks in the parent directory:
- Chapter 7: Multi-Agent (coordinate multiple agents)
- Chapter 14: RAG (query past incidents, runbooks)
- Chapter 15: Agent-to-Agent communication
- Chapter 18: Advanced guardrails

---

## Troubleshooting

### "API key not found"
```bash
# Make sure it's exported
echo $ANTHROPIC_API_KEY

# If empty, set it:
export ANTHROPIC_API_KEY="your-key-here"
```

### "Module not found"
```bash
# Install dependencies
pip install -r requirements.txt

# If using system Python, you might need:
pip install --user -r requirements.txt
```

### "Permission denied"
```bash
# Make scripts executable
chmod +x work-agent
chmod +x agents/*.py
chmod +x examples/*.py
```

### "File too large"
```bash
# Limit lines analyzed
python agents/log_analyzer.py --file large.log --lines 1000

# Or analyze just the tail
tail -1000 large.log | python agents/log_analyzer.py
```

---

## Get Help

- **API Docs:** https://docs.anthropic.com/
- **Pricing:** https://www.anthropic.com/pricing
- **This repo:** Check the notebooks for more patterns

---

## What You've Built

You now have:
✅ 3 production-ready AI agents
✅ 2 learning examples (simple → advanced)
✅ Unified CLI tool
✅ Integration with your workflow
✅ Understanding of AI agent patterns

**You can now:**
- Analyze logs in seconds instead of hours
- Review configs automatically
- Get help during incidents
- Ask DevOps questions anytime
- Build custom agents for your specific needs

**Next:**
- Use these daily at work
- Customize for your environment
- Build more specialized agents
- Maybe turn this into a startup product!

Ready to start? Run your first agent now:
```bash
python examples/01_simple_log_analyzer.py
```
