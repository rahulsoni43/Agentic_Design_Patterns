"""
Data Models for Sherlock SRE

These are the core data structures used throughout the system.
All models use Pydantic for validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class Severity(str, Enum):
    """Incident severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EventType(str, Enum):
    """Types of events we track"""
    POD_CRASH = "pod_crash"
    NODE_PRESSURE = "node_pressure"
    HIGH_MEMORY = "high_memory"
    HIGH_CPU = "high_cpu"
    ERROR_SPIKE = "error_spike"
    LATENCY_SPIKE = "latency_spike"
    DEPLOYMENT_FAILURE = "deployment_failure"
    NETWORK_ISSUE = "network_issue"
    UNKNOWN = "unknown"


class Event(BaseModel):
    """
    A single event from any source (K8s, logs, metrics, etc.)
    """
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime
    event_type: EventType
    source: str  # "kubernetes", "elasticsearch", "prometheus", etc.
    severity: Severity
    message: str
    resource: str  # "namespace/pod-name" or "service-name"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class Correlation(BaseModel):
    """
    A correlation between events
    """
    events: List[Event]
    correlation_type: str  # "temporal", "causal", "semantic"
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class RootCauseAnalysis(BaseModel):
    """
    AI-generated root cause analysis
    """
    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str]
    alternative_causes: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Action(BaseModel):
    """
    A recommended action to take
    """
    description: str
    command: Optional[str] = None  # Actual command to run
    risk_level: str  # "low", "medium", "high"
    expected_outcome: str
    verification_command: Optional[str] = None


class Investigation(BaseModel):
    """
    A complete investigation session
    """
    id: UUID = Field(default_factory=uuid4)
    query: str  # Original user query
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    events: List[Event] = Field(default_factory=list)
    correlations: List[Correlation] = Field(default_factory=list)
    analysis: Optional[RootCauseAnalysis] = None
    recommended_actions: List[Action] = Field(default_factory=list)
    status: str = "in_progress"  # "in_progress", "completed", "failed"
    user_id: Optional[str] = None
    resolution: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class HistoricalIncident(BaseModel):
    """
    A past incident stored for learning
    """
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    occurred_at: datetime
    resolved_at: Optional[datetime] = None
    severity: Severity

    # What happened
    symptoms: List[str]
    affected_services: List[str]
    error_messages: List[str] = Field(default_factory=list)

    # Analysis
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    resolution_steps: List[str] = Field(default_factory=list)

    # Metadata
    responders: List[str] = Field(default_factory=list)
    duration_minutes: Optional[int] = None
    mttr_minutes: Optional[int] = None  # Mean Time To Resolve

    # For RAG
    embedding: Optional[List[float]] = None
    similarity_score: Optional[float] = None  # When retrieved from vector search

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class PodStatus(BaseModel):
    """Kubernetes pod status"""
    name: str
    namespace: str
    status: str  # "Running", "Pending", "Failed", "CrashLoopBackOff"
    restarts: int
    age: str
    node: Optional[str] = None
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    container_statuses: List[Dict[str, Any]] = Field(default_factory=list)


class NodeStatus(BaseModel):
    """Kubernetes node status"""
    name: str
    status: str  # "Ready", "NotReady"
    roles: List[str]
    age: str
    version: str
    cpu_usage: Optional[str] = None
    memory_usage: Optional[str] = None
    conditions: List[Dict[str, Any]] = Field(default_factory=list)


class K8sClusterHealth(BaseModel):
    """Overall Kubernetes cluster health"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_nodes: int
    ready_nodes: int
    total_pods: int
    running_pods: int
    failed_pods: List[PodStatus] = Field(default_factory=list)
    crashlooping_pods: List[PodStatus] = Field(default_factory=list)
    pending_pods: List[PodStatus] = Field(default_factory=list)
    node_issues: List[NodeStatus] = Field(default_factory=list)
    recent_events: List[Event] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CollectorResult(BaseModel):
    """Result from a data collector"""
    collector_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool
    events: List[Event] = Field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
