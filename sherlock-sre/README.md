# Sherlock - AI-Powered SRE Investigation Copilot

**Your AI partner for incident investigation and troubleshooting**

> "Elementary, my dear Watson" - but for DevOps incidents

---

## 🎯 Problem

SRE/Support engineers waste 60-80% of their time on manual investigation:
- Checking 6+ different tools during incidents
- Running the same diagnostic commands repeatedly
- Trying to remember past similar incidents
- Manually correlating logs, metrics, and events
- Context switching that breaks mental flow

**Result:** 2+ hours investigating what should take 15 minutes

---

## 💡 Solution

Sherlock is an AI-powered investigation copilot that acts like a **senior SRE sitting next to you**, guiding you through incidents:

- 🔍 **Automatically correlates** logs, metrics, K8s events, cloud APIs
- 🧠 **Learns from past incidents** using RAG (Retrieval-Augmented Generation)
- 💬 **Conversational interface** via Slack (where you already work)
- ⚡ **Suggests root causes** with evidence and confidence scores
- 🛠️ **Provides exact commands** to run for investigation and remediation
- 📊 **Reduces MTTR** by 50-70% (Mean Time To Resolve)

---

## 🚀 Quick Example

```
You: "API is returning 502s in production"

Sherlock:
🔍 Investigating...

Found 3 related incidents:
• 2024-10-15: Same 502s → DB connection pool exhausted
• 2024-09-22: Similar pattern → Memory leak in auth service

Current analysis:
✓ Logs: 150 errors in last 5 min (auth-service)
✓ Metrics: Memory 95% on auth-service-pod-abc123
✓ K8s: Pod restarted 3x in last 10 min
✓ Pattern match: 90% similar to incident #2024-09-22

Likely root cause: Memory leak in auth service (85% confidence)

Recommended actions:
1. Check current state:
   kubectl get pods -n production | grep auth-service

2. Verify memory usage:
   kubectl top pod auth-service-abc123 -n production

3. Immediate fix (restart pod):
   kubectl delete pod auth-service-abc123 -n production

4. Scale for redundancy:
   kubectl scale deployment auth-service --replicas=5

Want me to execute? [Yes/Show more data/Escalate]
```

---

## ✨ Features

### Phase 1: K8s Investigation Assistant (Weeks 1-4)
- ✅ K8s cluster health monitoring
- ✅ Pod/Node/Event analysis
- ✅ AI-powered root cause suggestions
- ✅ Slack bot interface
- ✅ Historical incident pattern matching

### Phase 2: Cross-System Correlation (Weeks 5-8)
- 🔄 Log aggregation (Splunk, ELK, CloudWatch)
- 🔄 Metrics correlation (Datadog, Prometheus, Grafana)
- 🔄 APM integration (New Relic, Dynatrace)
- 🔄 Cloud API integration (AWS, Azure, GCP)
- 🔄 Timeline reconstruction

### Phase 3: Learning & Prediction (Weeks 9-12)
- 🔮 Predictive failure detection
- 🔮 Proactive alerts (before outages)
- 🔮 Auto-generated runbooks
- 🔮 Trend analysis and capacity planning

### Phase 4: Autonomous Actions (Weeks 13-16)
- 🤖 Auto-remediation (with guardrails)
- 🤖 Auto-rollback on bad deploys
- 🤖 Auto-scaling decisions
- 🤖 Self-healing workflows

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Systems                       │
│  K8s • Logs • Metrics • APM • Cloud APIs • Incidents       │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  Data Collectors (Parallel)                 │
│  ├─ K8s Collector (pods, nodes, events)                   │
│  ├─ Log Collector (errors, patterns)                      │
│  ├─ Metrics Collector (CPU, memory, latency)              │
│  └─ Incident Collector (past incidents)                   │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Analysis Engine (AI)                      │
│  ├─ Correlation Engine (find related signals)             │
│  ├─ Pattern Matcher (compare to past incidents)           │
│  ├─ Root Cause Analyzer (Claude AI reasoning)             │
│  └─ Recommendation Engine (suggest actions)               │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Knowledge Base (RAG)                     │
│  ├─ Vector DB (incident embeddings)                       │
│  ├─ Graph DB (service dependencies)                       │
│  └─ Time-series DB (historical patterns)                  │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  User Interface                             │
│  ├─ Slack Bot (primary - conversational)                  │
│  ├─ Web Dashboard (reports, analytics)                    │
│  └─ API (integrations, webhooks)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

```yaml
Language: Python 3.11+
Framework: FastAPI (async, production-ready)

AI/ML:
  - Anthropic Claude Sonnet 4.5 (reasoning, root cause analysis)
  - LangChain (agent orchestration)
  - Vector DB: Weaviate (semantic search of incidents)

Data Sources:
  - Kubernetes API (kubectl python client)
  - Prometheus (metrics)
  - Elasticsearch (logs)
  - AWS/Azure/GCP SDKs

Storage:
  - PostgreSQL (incidents, metadata)
  - Redis (caching, real-time data)
  - Weaviate (vector embeddings)

Interface:
  - Slack SDK (bot, webhooks)
  - React (web dashboard - optional)

Deployment:
  - Docker (containerized)
  - Kubernetes (production deployment)
  - Terraform (infrastructure as code)
```

---

## 📚 Project Structure

```
sherlock-sre/
├── README.md                    # This file
├── docs/
│   ├── ARCHITECTURE.md         # Detailed system design
│   ├── SETUP.md                # Setup and installation
│   └── DEVELOPMENT.md          # Development guide
├── src/
│   ├── collectors/             # Data collection modules
│   │   ├── k8s_collector.py
│   │   ├── log_collector.py
│   │   └── metrics_collector.py
│   ├── analyzers/              # AI analysis engines
│   │   ├── correlator.py
│   │   ├── pattern_matcher.py
│   │   └── root_cause_analyzer.py
│   ├── interfaces/             # User interfaces
│   │   ├── slack_bot.py
│   │   └── api.py
│   ├── storage/                # Data persistence
│   │   ├── vector_store.py
│   │   └── incident_store.py
│   └── main.py                 # Application entry point
├── tests/                      # Unit and integration tests
├── deploy/                     # Deployment configurations
│   ├── docker/
│   ├── kubernetes/
│   └── terraform/
├── requirements.txt            # Python dependencies
└── .env.example               # Environment variables template
```

---

## 🚦 Getting Started

```bash
# Clone the repository
git clone https://github.com/rahulsoni43/sherlock-sre.git
cd sherlock-sre

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run locally
python src/main.py

# Or use Docker
docker-compose up
```

---

## 🎯 Roadmap

### ✅ Phase 1: Foundation (Weeks 1-4)
- [x] Project setup and architecture
- [ ] K8s data collector
- [ ] Basic AI analysis
- [ ] Slack bot MVP
- [ ] First use case: Pod crashloop investigation

### 🔄 Phase 2: Multi-System (Weeks 5-8)
- [ ] Log collection and analysis
- [ ] Metrics correlation
- [ ] Cloud API integration
- [ ] Cross-system timeline

### 🔮 Phase 3: Intelligence (Weeks 9-12)
- [ ] RAG system for past incidents
- [ ] Predictive analysis
- [ ] Auto-generated runbooks
- [ ] Proactive alerts

### 🤖 Phase 4: Automation (Weeks 13-16)
- [ ] Auto-remediation framework
- [ ] Approval workflows
- [ ] Self-healing capabilities
- [ ] Incident post-mortems

---

## 💡 Why This Will Work

**Technical Excellence:**
- Staff Engineer-level architecture
- Production-ready from day one
- AI-powered, not rule-based
- Learns and improves over time

**Real Problem:**
- Every SRE team has this pain
- Measurable impact (reduced MTTR)
- Scales with team size

**Differentiation:**
- Not another dashboard
- Conversational, not charts
- Proactive, not reactive
- Contextual, not generic

---

## 📈 Success Metrics

- **MTTR Reduction**: 50-70% faster incident resolution
- **Time Saved**: 10+ hours/week per SRE
- **Incident Prevention**: Catch 80% of issues before outage
- **Knowledge Capture**: Every incident improves the system

---

## 🤝 Contributing

This is currently an internal project. Will be open-sourced once validated.

---

## 📄 License

MIT License (when open-sourced)

---

## 👤 Author

Built with ❤️ by an SRE who's tired of 3am pages for known issues.

**Goal:** Become the go-to Staff Engineer for impossible troubleshooting problems.

---

## 🔗 Links

- **Documentation**: [docs/](docs/)
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

**Status:** 🚧 In Development - Phase 1

**Last Updated:** November 2025
