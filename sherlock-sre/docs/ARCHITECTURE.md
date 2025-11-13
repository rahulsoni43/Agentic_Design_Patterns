# Sherlock SRE - System Architecture

**Staff Engineer-Level Design for AI-Powered Incident Investigation**

---

## Table of Contents
1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [System Components](#system-components)
4. [Data Flow](#data-flow)
5. [AI/ML Architecture](#aiml-architecture)
6. [Scalability](#scalability)
7. [Security](#security)
8. [Deployment](#deployment)

---

## Overview

Sherlock is designed as a **multi-agent, event-driven system** that continuously monitors infrastructure, learns from incidents, and provides intelligent investigation assistance.

### Key Characteristics
- **Real-time**: Sub-second response to queries
- **Scalable**: Handle 1000s of services, millions of events
- **Reliable**: 99.9% uptime (we can't go down during incidents!)
- **Secure**: Read-only access, audit logs, approval workflows
- **Intelligent**: Learns and improves over time

---

## Design Principles

### 1. **Composability over Monolith**
Each component is independent and replaceable:
- K8s collector can be swapped for different orchestrator
- Claude AI can be replaced with other LLMs
- Slack can be replaced with Teams/Discord

### 2. **Async-First**
- All I/O operations are async
- Non-blocking data collection
- Parallel processing where possible

### 3. **Fail-Safe Defaults**
- Never auto-remediate without approval (Phase 1-3)
- Degrade gracefully if AI unavailable
- Log everything for audit

### 4. **Observable**
- OpenTelemetry instrumentation
- Structured logging
- Metrics for all operations

### 5. **Cost-Conscious**
- Cache AI responses
- Deduplicate similar queries
- Use cheaper models for simple tasks

---

## System Components

### 1. Data Collectors (Parallel Agents)

**Purpose**: Gather data from various sources in parallel

```python
┌─────────────────────────────────────────┐
│         Collector Orchestrator          │
│  (Runs collectors in parallel)          │
└─────────────────────────────────────────┘
              ↓          ↓          ↓
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │   K8s    │  │   Logs   │  │ Metrics  │
   │Collector │  │Collector │  │Collector │
   └──────────┘  └──────────┘  └──────────┘
        ↓             ↓              ↓
   K8s API      Elasticsearch   Prometheus
```

**Implementation**:
```python
# src/collectors/base.py
class BaseCollector(ABC):
    @abstractmethod
    async def collect(self) -> CollectorResult:
        """Collect data from source"""
        pass

# src/collectors/orchestrator.py
class CollectorOrchestrator:
    async def collect_all(self) -> dict:
        """Run all collectors in parallel"""
        results = await asyncio.gather(
            self.k8s_collector.collect(),
            self.log_collector.collect(),
            self.metrics_collector.collect(),
            return_exceptions=True
        )
        return self.merge_results(results)
```

**Collectors**:
- `K8sCollector`: Pods, nodes, events, deployments
- `LogCollector`: Error patterns, stack traces
- `MetricsCollector`: CPU, memory, latency, error rates
- `IncidentCollector`: Historical incidents (for learning)
- `CloudCollector`: AWS/Azure/GCP resource state

### 2. Analysis Engine (AI-Powered)

**Purpose**: Correlate data, find patterns, suggest root causes

```python
┌─────────────────────────────────────────┐
│          Analysis Pipeline              │
└─────────────────────────────────────────┘
              ↓
   ┌──────────────────┐
   │   Correlator     │  ← Find related signals
   └──────────────────┘
              ↓
   ┌──────────────────┐
   │ Pattern Matcher  │  ← Compare to past incidents
   └──────────────────┘
              ↓
   ┌──────────────────┐
   │ Root Cause AI    │  ← Claude reasoning
   └──────────────────┘
              ↓
   ┌──────────────────┐
   │ Recommendation   │  ← Suggest actions
   └──────────────────┘
```

**Correlation Logic**:
```python
# src/analyzers/correlator.py
class EventCorrelator:
    """
    Correlates events across time and systems

    Uses:
    1. Temporal correlation (events near in time)
    2. Causal correlation (A causes B)
    3. Semantic correlation (similar patterns)
    """

    def correlate(self, events: List[Event]) -> List[Correlation]:
        # Time-based: events within ±5 minutes
        temporal = self.find_temporal_correlations(events)

        # Dependency graph: service A calls service B
        causal = self.find_causal_correlations(events)

        # Vector similarity: similar error messages
        semantic = self.find_semantic_correlations(events)

        return self.merge_correlations(temporal, causal, semantic)
```

**Pattern Matching**:
```python
# src/analyzers/pattern_matcher.py
class PatternMatcher:
    """
    Compares current incident to historical patterns

    Uses RAG (Retrieval-Augmented Generation):
    1. Embed current incident
    2. Vector search in past incidents
    3. Return top-k similar incidents
    """

    async def find_similar_incidents(
        self,
        current: Incident
    ) -> List[HistoricalIncident]:
        # Create embedding
        embedding = await self.embed_incident(current)

        # Vector search
        similar = await self.vector_store.search(
            embedding,
            limit=5,
            min_similarity=0.7
        )

        return similar
```

**Root Cause Analysis**:
```python
# src/analyzers/root_cause_analyzer.py
class RootCauseAnalyzer:
    """
    Uses Claude AI for reasoning about root causes

    Approach:
    1. Gather all correlated events
    2. Retrieve similar past incidents
    3. Prompt Claude with structured data
    4. Parse and validate response
    """

    async def analyze(
        self,
        incident: Incident,
        correlations: List[Correlation],
        similar_past: List[HistoricalIncident]
    ) -> RootCauseAnalysis:

        prompt = self.build_analysis_prompt(
            incident=incident,
            correlations=correlations,
            similar_past=similar_past
        )

        response = await self.claude.analyze(prompt)

        # Structured output with confidence scores
        return RootCauseAnalysis(
            root_cause=response.root_cause,
            confidence=response.confidence,
            evidence=response.evidence,
            alternative_causes=response.alternatives
        )
```

### 3. Knowledge Base (RAG System)

**Purpose**: Store and retrieve past incidents for learning

```python
┌─────────────────────────────────────────┐
│           Knowledge Base                │
├─────────────────────────────────────────┤
│  Vector DB (Weaviate)                   │
│  - Incident embeddings                  │
│  - Semantic search                      │
├─────────────────────────────────────────┤
│  Graph DB (PostgreSQL + pg_graph)      │
│  - Service dependencies                 │
│  - Cause-effect relationships           │
├─────────────────────────────────────────┤
│  Time-Series DB (TimescaleDB)           │
│  - Metric history                       │
│  - Trend analysis                       │
└─────────────────────────────────────────┘
```

**Schema**:
```python
# src/storage/models.py
class Incident(BaseModel):
    """Incident data model"""
    id: UUID
    timestamp: datetime
    title: str
    description: str
    severity: Severity

    # What happened
    symptoms: List[str]
    affected_services: List[str]
    error_messages: List[str]

    # Analysis
    root_cause: Optional[str]
    resolution: Optional[str]

    # Metadata
    responders: List[str]
    duration_minutes: int
    mttr_minutes: int

    # For RAG
    embedding: Optional[List[float]]  # Vector representation

class ServiceDependency(BaseModel):
    """Service dependency graph"""
    from_service: str
    to_service: str
    dependency_type: DependencyType  # CALLS, DEPENDS_ON, STORES_IN
    latency_p50: float
    error_rate: float
```

### 4. User Interfaces

**Primary: Slack Bot** (conversational)

```python
# src/interfaces/slack_bot.py
class SherlockSlackBot:
    """
    Slack bot for conversational investigation

    Commands:
    - "investigate <symptom>" - Start investigation
    - "show evidence" - Display correlated events
    - "execute <action>" - Run remediation (with approval)
    - "learn from this" - Save incident to knowledge base
    """

    @app.event("app_mention")
    async def handle_mention(self, event, say):
        # Parse user query
        query = self.parse_query(event["text"])

        # Run investigation
        result = await self.investigator.investigate(query)

        # Format response
        message = self.format_slack_message(result)

        # Send to Slack
        await say(blocks=message)
```

**Secondary: Web Dashboard** (reports, analytics)

```python
# src/interfaces/api.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/incidents")
async def list_incidents():
    """List recent incidents"""
    pass

@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Get incident details"""
    pass

@app.get("/analytics/mttr")
async def get_mttr_trends():
    """Get MTTR trends over time"""
    pass
```

---

## Data Flow

### Investigation Flow

```
User asks question in Slack
         ↓
Parse query & intent
         ↓
Trigger collectors (parallel)
         ↓
├─ K8s: Get pods, events
├─ Logs: Search for errors
├─ Metrics: Check thresholds
└─ Incidents: Find similar past issues
         ↓
Correlate all data
         ↓
Send to Claude AI for analysis
         ↓
Generate recommendations
         ↓
Format for Slack
         ↓
Send response with actions
         ↓
[User approves action]
         ↓
Execute remediation
         ↓
Monitor outcome
         ↓
Save to knowledge base
```

### Learning Flow

```
Incident occurs
         ↓
Sherlock assists investigation
         ↓
Incident resolved
         ↓
Capture:
├─ What happened (symptoms)
├─ What was found (evidence)
├─ What was the cause (root cause)
└─ What fixed it (resolution)
         ↓
Create embedding
         ↓
Store in Vector DB
         ↓
Update service dependency graph
         ↓
Next time: Better, faster diagnosis
```

---

## AI/ML Architecture

### Model Selection

**Primary: Claude Sonnet 4.5**
- Best reasoning capabilities
- Handles complex troubleshooting logic
- Good at structured output
- Cost: ~$3 per million tokens

**For Embeddings: text-embedding-3-small** (OpenAI)
- Cheaper than Claude for embeddings
- Good performance
- Cost: ~$0.02 per million tokens

### Prompt Engineering

**Analysis Prompt Structure**:
```python
ANALYSIS_PROMPT = """
You are an expert SRE analyzing a production incident.

# CURRENT INCIDENT
Timestamp: {timestamp}
Symptoms: {symptoms}
Affected Services: {services}

# CORRELATED EVENTS (within ±5 min)
{correlated_events}

# SIMILAR PAST INCIDENTS
{past_incidents}

# SERVICE DEPENDENCIES
{dependency_graph}

# YOUR TASK
1. Analyze the evidence
2. Determine the most likely root cause (with confidence %)
3. List supporting evidence
4. Suggest 3-5 diagnostic steps
5. Recommend remediation actions

# OUTPUT FORMAT (JSON)
{{
  "root_cause": "...",
  "confidence": 0.85,
  "evidence": ["...", "..."],
  "diagnostic_steps": ["...", "..."],
  "remediation": ["...", "..."],
  "alternative_causes": ["...", "..."]
}}

ONLY return valid JSON.
"""
```

### Caching Strategy

```python
# Cache AI responses for similar queries
class AICache:
    """
    Cache Claude responses to save costs

    Cache key: hash(prompt + recent context)
    TTL: 1 hour

    Savings: ~70% of AI costs
    """

    async def get_or_generate(self, prompt: str) -> str:
        cache_key = self.hash_prompt(prompt)

        # Check cache
        cached = await self.redis.get(cache_key)
        if cached:
            return cached

        # Generate
        response = await self.claude.generate(prompt)

        # Cache
        await self.redis.setex(cache_key, 3600, response)

        return response
```

---

## Scalability

### Horizontal Scaling

```
┌────────────────────────────────────────┐
│         Load Balancer (K8s Service)    │
└────────────────────────────────────────┘
              ↓          ↓          ↓
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ Sherlock │  │ Sherlock │  │ Sherlock │
   │  Pod 1   │  │  Pod 2   │  │  Pod 3   │
   └──────────┘  └──────────┘  └──────────┘
        ↓             ↓              ↓
   ┌─────────────────────────────────────┐
   │      Shared Storage (Postgres)      │
   │      Shared Cache (Redis)           │
   │      Shared Vectors (Weaviate)      │
   └─────────────────────────────────────┘
```

### Performance Targets

- Query latency: < 2 seconds (p95)
- Concurrent investigations: 100+
- Events processed: 1M+ per hour
- Incident storage: Millions
- Vector search: < 100ms

### Resource Requirements

**Phase 1 (Single Cluster)**:
- CPU: 2 cores
- Memory: 4GB
- Storage: 50GB

**Phase 4 (Multi-Cluster, High Scale)**:
- CPU: 8 cores
- Memory: 16GB
- Storage: 500GB

---

## Security

### Principle: Read-Only by Default

- No write access to production systems (Phase 1-3)
- Only read K8s, logs, metrics
- Auto-remediation requires explicit approval

### Authentication & Authorization

```python
# RBAC for Slack commands
PERMISSIONS = {
    "investigate": ["sre", "oncall", "engineer"],
    "execute": ["sre", "oncall"],  # Requires higher privileges
    "admin": ["sre-lead"]
}
```

### Audit Logging

```python
# Every action is logged
class AuditLogger:
    def log_action(self, action: Action):
        self.log({
            "timestamp": datetime.utcnow(),
            "user": action.user,
            "action": action.type,
            "target": action.target,
            "result": action.result,
            "approved_by": action.approver
        })
```

### Secrets Management

- API keys in Kubernetes Secrets
- Never logged or exposed
- Rotated regularly

---

## Deployment

### Development

```bash
docker-compose up
```

### Production (Kubernetes)

```yaml
# deploy/kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sherlock-sre
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: sherlock
        image: sherlock-sre:latest
        resources:
          requests:
            cpu: 1
            memory: 2Gi
          limits:
            cpu: 2
            memory: 4Gi
```

### Observability

- **Logs**: Structured JSON to stdout → ELK stack
- **Metrics**: Prometheus /metrics endpoint
- **Traces**: OpenTelemetry → Jaeger
- **Alerts**: Alert if Sherlock is down (ironic!)

---

## Trade-offs & Decisions

### Why FastAPI over Flask?
- Async support (critical for parallel collection)
- Built-in type validation (Pydantic)
- Auto-generated API docs

### Why PostgreSQL over MongoDB?
- ACID transactions (incident data integrity)
- Complex queries (graph traversal)
- TimescaleDB extension (time-series)

### Why Weaviate over Pinecone?
- Self-hosted option (data sovereignty)
- Hybrid search (vector + keyword)
- GraphQL API

### Why Slack over Web UI?
- SREs already live in Slack
- Context switching is expensive
- Faster than opening dashboard

---

## Future Enhancements

### Phase 5: Advanced AI
- Fine-tuned models on our incidents
- Multi-model approach (Claude + specialized models)
- Reinforcement learning from feedback

### Phase 6: Multi-Tenancy
- Support multiple teams/clusters
- Isolated knowledge bases
- Custom runbooks per team

### Phase 7: Marketplace
- Community-contributed collectors
- Shared incident patterns
- Best practices library

---

**This architecture is designed to be Staff Engineer-level:**
- Production-ready from day one
- Scalable and maintainable
- Observable and debuggable
- Secure by default
- Cost-conscious

Every decision is documented and justified.
Every component can be replaced.
Every failure mode is considered.

---

**Next**: See [DEVELOPMENT.md](DEVELOPMENT.md) for implementation guide.
