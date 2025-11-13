# Kubernetes AI Monitoring Agent 🤖

**Proactive cluster monitoring powered by AI - Detect issues before they cause outages!**

## What This Does

✅ Monitors your AKS/EKS cluster 24/7
✅ **Predicts issues before outages** using AI
✅ Sends rich alerts to Slack with fix recommendations
✅ Provides actual kubectl commands to resolve issues
✅ Learns your cluster's normal behavior patterns
✅ Zero configuration needed (works out of the box)

### Why This is Different

| Traditional Monitoring | This AI Agent |
|----------------------|---------------|
| Alerts **after** things break | **Predicts before** outage |
| "Pod is crashlooping" | "Pod will OOM in 10 min - increase memory to 1Gi" |
| Fixed thresholds | AI learns your patterns |
| Noisy alerts | Smart deduplication |
| "What's wrong?" | "What's wrong + How to fix + Exact commands" |

---

## Quick Start (5 Minutes)

### Prerequisites

- Kubernetes cluster (AKS, EKS, GKE, or any K8s)
- kubectl configured and working
- Python 3.11+
- Anthropic API key (get free at https://console.anthropic.com/)
- Slack webhook (optional, but recommended)

### Setup

```bash
# 1. Clone/navigate to the project
cd /home/user/Agentic_Design_Patterns/k8s_monitoring_agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env and add your API keys

# 4. Test it works
python src/monitor.py --test

# 5. Run once to see results
python src/monitor.py --once

# 6. Start continuous monitoring
python src/monitor.py --interval 60
```

That's it! You'll now get Slack alerts when issues are detected.

---

## Configuration

### Get Your API Keys

**1. Anthropic API Key** (Required)
```bash
# Go to: https://console.anthropic.com/
# Sign up (free tier available)
# Create API key
# Add to .env:
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

**2. Slack Webhook** (Recommended)
```bash
# Go to: https://api.slack.com/messaging/webhooks
# Create incoming webhook
# Choose channel (e.g., #k8s-alerts)
# Copy webhook URL
# Add to .env:
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Recommended
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxxxx

# Optional
CLUSTER_NAME=my-prod-cluster  # Shown in alerts
```

---

## Usage

### Local Development / Testing

```bash
# Test integration (verify kubectl, AI, Slack all work)
python src/monitor.py --test

# Run once and exit
python src/monitor.py --once

# Continuous monitoring (every 60 seconds)
python src/monitor.py --interval 60

# Custom cluster name
python src/monitor.py --cluster prod-eks --interval 120
```

### Deploy to Kubernetes (Recommended)

**Option 1: As a Deployment (continuous monitoring)**

```bash
# 1. Build Docker image
docker build -t k8s-monitor:latest -f deploy/Dockerfile .

# If using private registry
docker tag k8s-monitor:latest your-registry.com/k8s-monitor:latest
docker push your-registry.com/k8s-monitor:latest

# 2. Create secrets with your API keys
kubectl create namespace monitoring

kubectl create secret generic k8s-monitor-secrets \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-your-key \
  --from-literal=SLACK_WEBHOOK_URL=https://hooks.slack.com/your-webhook \
  -n monitoring

# 3. Update deploy/kubernetes.yaml
# - Change image name if using private registry
# - Set your cluster name in ConfigMap

# 4. Deploy
kubectl apply -f deploy/kubernetes.yaml

# 5. Check logs
kubectl logs -f -n monitoring deployment/k8s-monitor
```

**Option 2: As a CronJob (scheduled checks)**

```bash
# Edit deploy/kubernetes.yaml and uncomment the CronJob section
# Then deploy (it's included in the same file)

kubectl apply -f deploy/kubernetes.yaml

# View CronJob
kubectl get cronjobs -n monitoring

# View recent jobs
kubectl get jobs -n monitoring
```

### Deploy Outside Cluster

```bash
# On a VM, laptop, or cloud function
# Make sure kubectl is configured

# Run continuously in background
nohup python src/monitor.py --interval 120 > monitor.log 2>&1 &

# Or use systemd, supervisor, etc.
```

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────┐
│   K8s Cluster (Your AKS/EKS)           │
│   - Pods, Nodes, Events, Resources      │
└─────────────────────────────────────────┘
                 ↓ kubectl
┌─────────────────────────────────────────┐
│   Data Collectors (Parallel)            │
│   - Pod health, Node status, Events     │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│   AI Analyzer (Claude Sonnet 4.5)      │
│   - Detect anomalies                    │
│   - Predict failures                    │
│   - Generate recommendations            │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│   Alert Manager                         │
│   - Smart deduplication                 │
│   - Severity classification             │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│   Slack Notification                    │
│   - Rich formatting                     │
│   - Actionable commands                 │
└─────────────────────────────────────────┘
```

### What Gets Monitored

- ✅ Pod health (crashes, restarts, pending, failed)
- ✅ Node status (ready, pressure, taints)
- ✅ Events (warnings, errors, patterns)
- ✅ Resource usage (CPU, memory if metrics-server installed)
- ✅ Deployments, StatefulSets, DaemonSets
- ✅ HPA status
- ✅ PVC issues

### What You Get in Alerts

**Example Slack Alert:**

```
🔴 CRITICAL: my-prod-cluster Health Alert

Issues Detected:
• CrashLoopBackOff - production/api-server-abc123
  Pod restarted 15 times in 10 minutes. Memory at 99%.
  Impact: degraded | Severity: HIGH

🔮 Predictions:
• Node will run out of memory (in 15-30 minutes)
  Confidence: high | Impact: Pod evictions, service degradation

🔧 Recommended Actions:
1. Increase memory limit for api-server (Priority: P0)
   kubectl set resources deployment api-server -n production --limits=memory=1Gi
   Risk: low

Cluster Status:
Pods: 50 (2 issues)
Nodes: 3/3 ready
```

---

## AI Patterns Used

This agent demonstrates patterns from "Agentic Design Patterns" book:

1. **Multi-Agent (Ch 7):** Separate collectors for pods, nodes, events
2. **Parallelization (Ch 3):** Collect data concurrently
3. **Tool Use (Ch 5):** Execute kubectl commands
4. **Planning (Ch 6):** Generate remediation plans
5. **Reflection (Ch 4):** Validate recommendations before sending
6. **Guardrails (Ch 18):** Alert deduplication, rate limiting
7. **Human-in-Loop (Ch 13):** Slack escalation

---

## Customization

### Adjust Monitoring Interval

```bash
# Check every 30 seconds (more frequent)
python src/monitor.py --interval 30

# Check every 5 minutes (less frequent, lower cost)
python src/monitor.py --interval 300
```

### Customize AI Analysis

Edit `src/ai_analyzer.py` and modify the prompts to:
- Focus on specific namespaces
- Prioritize certain types of issues
- Add company-specific runbooks
- Integrate with your tools

### Add More Data Sources

Edit `src/k8s_collector.py` to collect:
- Custom metrics from Prometheus
- Application-specific health checks
- Cost data from cloud provider
- External dependencies status

---

## Cost Estimates

**API Costs (Anthropic Claude Sonnet 4.5):**
- Per health check: ~$0.10 - $0.30
- Every 60s (1440/day): ~$140 - $430/month
- Every 300s (288/day): ~$30 - $85/month

**Optimization tips:**
1. Increase interval (5 min = 80% cost reduction)
2. Use CronJob instead of continuous
3. Only alert on WARNING/CRITICAL (skip INFO)
4. Use cheaper model (Haiku) for simple checks

**ROI Calculation:**
- 1 hour downtime prevented = $5k-100k saved (typically)
- Agent cost = $50-200/month
- ROI = 25x-2000x

---

## Troubleshooting

### "kubectl: command not found"

```bash
# Install kubectl
# https://kubernetes.io/docs/tasks/tools/

# Verify it works
kubectl get pods
```

### "No cluster data collected"

```bash
# Check kubectl access
kubectl auth can-i get pods --all-namespaces

# Should return "yes"
# If "no", you need RBAC permissions
```

### "Slack notifications not sending"

```bash
# Test webhook manually
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test"}' \
  YOUR_SLACK_WEBHOOK_URL

# If that works, check your .env file
echo $SLACK_WEBHOOK_URL
```

### "AI analysis failed"

```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Test API manually
python -c "from anthropic import Anthropic; print(Anthropic().messages.create(model='claude-sonnet-4-5-20250929', max_tokens=10, messages=[{'role':'user','content':'hi'}]))"
```

---

## Security

**RBAC Permissions:**
- Read-only access to cluster resources
- No write permissions (safe to run)
- See `deploy/kubernetes.yaml` for full RBAC config

**Secrets:**
- API keys stored in Kubernetes Secrets
- Not logged or exposed
- Mounted as environment variables

**Network:**
- Outbound only (to Anthropic API, Slack)
- No inbound connections needed

---

## Roadmap / Future Features

**Phase 1 (Current - MVP):**
- ✅ Basic health monitoring
- ✅ AI anomaly detection
- ✅ Slack alerts

**Phase 2 (Next 2 months):**
- [ ] Historical baseline learning (RAG)
- [ ] Multi-cluster support
- [ ] Custom metrics integration (Prometheus)
- [ ] Web dashboard

**Phase 3 (Future):**
- [ ] Auto-remediation (with approval)
- [ ] Cost optimization insights
- [ ] Capacity planning predictions
- [ ] Integration with PagerDuty, OpsGenie
- [ ] Incident timeline reconstruction

---

## Business Opportunity

**This could be a SaaS product:**

**Target Market:**
- Companies with Kubernetes (millions worldwide)
- SRE/DevOps teams (always short-staffed)
- High cost of downtime ($5k-100k/hour)

**Pricing Model:**
- $299-999/month per cluster
- $2999-9999/month enterprise (multi-cluster)

**Competition:**
- Datadog, New Relic: Generic monitoring, no AI predictions
- PagerDuty: Incident management, no prevention
- Our edge: AI-powered prediction + actionable recommendations

**MVP to Revenue Timeline:**
- Week 1-4: Polish UI, add features
- Week 5-8: Get 5-10 beta users
- Week 9-12: Launch, first paying customer
- Month 4-6: 20-50 customers = $10k-50k MRR

---

## Contributing

This is a learning project demonstrating AI agent patterns.

**Ways to improve:**
1. Add more data collectors (Prometheus, cloud provider APIs)
2. Improve AI prompts for better predictions
3. Add auto-remediation with safety checks
4. Build a web dashboard
5. Support more notification channels (PagerDuty, email, etc.)

---

## Support

**Questions? Ideas?**
- Open an issue on GitHub
- Check the docs in `docs/ARCHITECTURE.md`
- Study the code (well commented!)

---

## License

MIT License - Feel free to use, modify, commercialize!

---

## Acknowledgments

Built using patterns from:
- **"Agentic Design Patterns"** by Antonio Gulli
- Anthropic Claude Sonnet 4.5
- Kubernetes

---

**Ready to prevent outages? Start monitoring:**

```bash
python src/monitor.py --test
python src/monitor.py --once
python src/monitor.py --interval 60
```

🚀 **Save time. Prevent outages. Sleep better.** 🚀
