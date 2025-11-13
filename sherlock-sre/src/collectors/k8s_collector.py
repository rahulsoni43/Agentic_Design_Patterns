"""
Kubernetes Data Collector

Collects health data from Kubernetes clusters.
Uses kubernetes-python client for API access.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from kubernetes import client, config as k8s_config
from kubernetes.client.rest import ApiException

from .base import BaseCollector
from ..models import (
    CollectorResult,
    Event,
    EventType,
    Severity,
    PodStatus,
    NodeStatus,
    K8sClusterHealth
)
from ..config import settings

logger = logging.getLogger(__name__)


class K8sCollector(BaseCollector):
    """
    Collects data from Kubernetes API

    Monitors:
    - Pod health (crashes, restarts, pending, failed)
    - Node status (ready, pressure, taints)
    - Events (warnings, errors)
    - Resource usage (if metrics-server available)
    """

    def __init__(self):
        super().__init__("k8s_collector")
        self._api_client: Optional[client.ApiClient] = None
        self._core_v1: Optional[client.CoreV1Api] = None
        self._apps_v1: Optional[client.AppsV1Api] = None
        self._initialized = False

    async def _initialize(self):
        """Initialize Kubernetes client"""
        if self._initialized:
            return

        try:
            # Load config
            if settings.kubeconfig_path:
                k8s_config.load_kube_config(config_file=settings.kubeconfig_path)
            else:
                try:
                    # Try in-cluster config first
                    k8s_config.load_incluster_config()
                except k8s_config.ConfigException:
                    # Fall back to default kubeconfig
                    k8s_config.load_kube_config()

            self._api_client = client.ApiClient()
            self._core_v1 = client.CoreV1Api(self._api_client)
            self._apps_v1 = client.AppsV1Api(self._api_client)
            self._initialized = True

            self.logger.info("Kubernetes client initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    async def collect(self, query: Optional[str] = None) -> CollectorResult:
        """
        Collect Kubernetes cluster health data

        Args:
            query: Optional query to filter collection (e.g., "namespace:production")

        Returns:
            CollectorResult with K8s events
        """
        try:
            await self._initialize()

            events: List[Event] = []

            # Collect pod health
            pod_events = await self._collect_pod_health(query)
            events.extend(pod_events)

            # Collect node health
            node_events = await self._collect_node_health()
            events.extend(node_events)

            # Collect K8s events
            k8s_events = await self._collect_events()
            events.extend(k8s_events)

            return CollectorResult(
                collector_name=self.name,
                success=True,
                events=events,
                metadata={
                    "total_events": len(events),
                    "query": query
                }
            )

        except Exception as e:
            self.logger.error(f"Collection failed: {e}", exc_info=True)
            return CollectorResult(
                collector_name=self.name,
                success=False,
                events=[],
                error=str(e)
            )

    async def _collect_pod_health(self, query: Optional[str]) -> List[Event]:
        """Collect pod health events"""
        events: List[Event] = []

        try:
            # Get all pods
            pods = self._core_v1.list_pod_for_all_namespaces(timeout_seconds=30)

            for pod in pods.items:
                # Filter by namespace if query specifies
                if query and "namespace:" in query:
                    target_ns = query.split("namespace:")[1].split()[0]
                    if pod.metadata.namespace != target_ns:
                        continue

                pod_name = pod.metadata.name
                namespace = pod.metadata.namespace
                phase = pod.status.phase

                # Check for crashlooping
                for container_status in (pod.status.container_statuses or []):
                    restart_count = container_status.restart_count or 0

                    # High restart count
                    if restart_count > 5:
                        events.append(Event(
                            timestamp=datetime.utcnow(),
                            event_type=EventType.POD_CRASH,
                            source="kubernetes",
                            severity=Severity.HIGH if restart_count > 10 else Severity.MEDIUM,
                            message=f"Pod {pod_name} has {restart_count} restarts",
                            resource=f"{namespace}/{pod_name}",
                            metadata={
                                "container": container_status.name,
                                "restart_count": restart_count,
                                "phase": phase
                            }
                        ))

                    # CrashLoopBackOff
                    if container_status.state and container_status.state.waiting:
                        reason = container_status.state.waiting.reason
                        if "CrashLoopBackOff" in reason or "Error" in reason:
                            events.append(Event(
                                timestamp=datetime.utcnow(),
                                event_type=EventType.POD_CRASH,
                                source="kubernetes",
                                severity=Severity.CRITICAL,
                                message=f"Pod {pod_name} is {reason}",
                                resource=f"{namespace}/{pod_name}",
                                metadata={
                                    "container": container_status.name,
                                    "reason": reason,
                                    "message": container_status.state.waiting.message or ""
                                }
                            ))

                    # OOMKilled
                    if container_status.last_state and container_status.last_state.terminated:
                        if container_status.last_state.terminated.reason == "OOMKilled":
                            events.append(Event(
                                timestamp=datetime.utcnow(),
                                event_type=EventType.HIGH_MEMORY,
                                source="kubernetes",
                                severity=Severity.HIGH,
                                message=f"Pod {pod_name} was OOMKilled",
                                resource=f"{namespace}/{pod_name}",
                                metadata={
                                    "container": container_status.name,
                                    "exit_code": container_status.last_state.terminated.exit_code
                                }
                            ))

                # Pending pods
                if phase == "Pending":
                    # Check how long it's been pending
                    created = pod.metadata.creation_timestamp
                    age = datetime.now(created.tzinfo) - created

                    if age > timedelta(minutes=5):
                        events.append(Event(
                            timestamp=datetime.utcnow(),
                            event_type=EventType.DEPLOYMENT_FAILURE,
                            source="kubernetes",
                            severity=Severity.MEDIUM,
                            message=f"Pod {pod_name} pending for {age.seconds // 60} minutes",
                            resource=f"{namespace}/{pod_name}",
                            metadata={
                                "phase": phase,
                                "conditions": [c.to_dict() for c in (pod.status.conditions or [])]
                            }
                        ))

                # Failed pods
                if phase == "Failed":
                    events.append(Event(
                        timestamp=datetime.utcnow(),
                        event_type=EventType.POD_CRASH,
                        source="kubernetes",
                        severity=Severity.HIGH,
                        message=f"Pod {pod_name} failed",
                        resource=f"{namespace}/{pod_name}",
                        metadata={
                            "phase": phase,
                            "reason": pod.status.reason or "Unknown"
                        }
                    ))

        except ApiException as e:
            self.logger.error(f"K8s API error collecting pods: {e}")
        except Exception as e:
            self.logger.error(f"Error collecting pod health: {e}", exc_info=True)

        return events

    async def _collect_node_health(self) -> List[Event]:
        """Collect node health events"""
        events: List[Event] = []

        try:
            nodes = self._core_v1.list_node(timeout_seconds=30)

            for node in nodes.items:
                node_name = node.metadata.name

                # Check conditions
                for condition in (node.status.conditions or []):
                    condition_type = condition.type
                    status = condition.status

                    # Node not ready
                    if condition_type == "Ready" and status != "True":
                        events.append(Event(
                            timestamp=datetime.utcnow(),
                            event_type=EventType.NODE_PRESSURE,
                            source="kubernetes",
                            severity=Severity.CRITICAL,
                            message=f"Node {node_name} is NotReady",
                            resource=f"node/{node_name}",
                            metadata={
                                "reason": condition.reason or "",
                                "message": condition.message or ""
                            }
                        ))

                    # Pressure conditions
                    pressure_conditions = ["MemoryPressure", "DiskPressure", "PIDPressure"]
                    if condition_type in pressure_conditions and status == "True":
                        events.append(Event(
                            timestamp=datetime.utcnow(),
                            event_type=EventType.NODE_PRESSURE,
                            source="kubernetes",
                            severity=Severity.HIGH,
                            message=f"Node {node_name} has {condition_type}",
                            resource=f"node/{node_name}",
                            metadata={
                                "condition": condition_type,
                                "message": condition.message or ""
                            }
                        ))

                # Check taints (cordoned nodes)
                if node.spec.taints:
                    for taint in node.spec.taints:
                        if taint.effect == "NoSchedule":
                            events.append(Event(
                                timestamp=datetime.utcnow(),
                                event_type=EventType.NODE_PRESSURE,
                                source="kubernetes",
                                severity=Severity.MEDIUM,
                                message=f"Node {node_name} is tainted/cordoned",
                                resource=f"node/{node_name}",
                                metadata={
                                    "key": taint.key,
                                    "value": taint.value or "",
                                    "effect": taint.effect
                                }
                            ))

        except ApiException as e:
            self.logger.error(f"K8s API error collecting nodes: {e}")
        except Exception as e:
            self.logger.error(f"Error collecting node health: {e}", exc_info=True)

        return events

    async def _collect_events(self, lookback_minutes: int = 10) -> List[Event]:
        """Collect Kubernetes events (warnings, errors)"""
        events: List[Event] = []

        try:
            # Get events from last N minutes
            k8s_events = self._core_v1.list_event_for_all_namespaces(timeout_seconds=30)

            cutoff_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)

            for k8s_event in k8s_events.items:
                # Filter by time
                if k8s_event.last_timestamp:
                    event_time = k8s_event.last_timestamp.replace(tzinfo=None)
                    if event_time < cutoff_time:
                        continue

                # Only care about warnings and errors
                if k8s_event.type not in ["Warning", "Error"]:
                    continue

                # Map K8s event to our Event
                severity = Severity.HIGH if k8s_event.type == "Error" else Severity.MEDIUM

                # Determine event type based on reason
                event_type = self._map_k8s_event_reason(k8s_event.reason)

                events.append(Event(
                    timestamp=k8s_event.last_timestamp.replace(tzinfo=None) if k8s_event.last_timestamp else datetime.utcnow(),
                    event_type=event_type,
                    source="kubernetes",
                    severity=severity,
                    message=k8s_event.message or k8s_event.reason,
                    resource=f"{k8s_event.involved_object.namespace}/{k8s_event.involved_object.name}",
                    metadata={
                        "reason": k8s_event.reason,
                        "count": k8s_event.count or 1,
                        "kind": k8s_event.involved_object.kind
                    }
                ))

        except ApiException as e:
            self.logger.error(f"K8s API error collecting events: {e}")
        except Exception as e:
            self.logger.error(f"Error collecting K8s events: {e}", exc_info=True)

        return events

    def _map_k8s_event_reason(self, reason: str) -> EventType:
        """Map Kubernetes event reason to our EventType"""
        reason_lower = reason.lower()

        if "backoff" in reason_lower or "crash" in reason_lower:
            return EventType.POD_CRASH
        elif "oom" in reason_lower or "memory" in reason_lower:
            return EventType.HIGH_MEMORY
        elif "cpu" in reason_lower:
            return EventType.HIGH_CPU
        elif "failed" in reason_lower:
            return EventType.DEPLOYMENT_FAILURE
        elif "network" in reason_lower or "connection" in reason_lower:
            return EventType.NETWORK_ISSUE
        else:
            return EventType.UNKNOWN

    async def get_cluster_health(self) -> K8sClusterHealth:
        """
        Get overall cluster health summary

        Returns:
            K8sClusterHealth with comprehensive status
        """
        await self._initialize()

        try:
            # Get all pods
            pods = self._core_v1.list_pod_for_all_namespaces(timeout_seconds=30)
            total_pods = len(pods.items)
            running_pods = len([p for p in pods.items if p.status.phase == "Running"])

            failed_pods: List[PodStatus] = []
            crashlooping_pods: List[PodStatus] = []
            pending_pods: List[PodStatus] = []

            for pod in pods.items:
                if pod.status.phase == "Failed":
                    failed_pods.append(self._pod_to_status(pod))
                elif pod.status.phase == "Pending":
                    pending_pods.append(self._pod_to_status(pod))

                # Check for crashlooping
                for cs in (pod.status.container_statuses or []):
                    if cs.state and cs.state.waiting:
                        if "CrashLoopBackOff" in (cs.state.waiting.reason or ""):
                            crashlooping_pods.append(self._pod_to_status(pod))
                            break

            # Get nodes
            nodes = self._core_v1.list_node(timeout_seconds=30)
            total_nodes = len(nodes.items)
            ready_nodes = 0
            node_issues: List[NodeStatus] = []

            for node in nodes.items:
                is_ready = False
                for condition in (node.status.conditions or []):
                    if condition.type == "Ready" and condition.status == "True":
                        is_ready = True
                        ready_nodes += 1
                        break

                if not is_ready:
                    node_issues.append(self._node_to_status(node))

            # Get recent events
            result = await self.collect()

            return K8sClusterHealth(
                total_nodes=total_nodes,
                ready_nodes=ready_nodes,
                total_pods=total_pods,
                running_pods=running_pods,
                failed_pods=failed_pods,
                crashlooping_pods=crashlooping_pods,
                pending_pods=pending_pods,
                node_issues=node_issues,
                recent_events=result.events
            )

        except Exception as e:
            self.logger.error(f"Error getting cluster health: {e}", exc_info=True)
            raise

    def _pod_to_status(self, pod) -> PodStatus:
        """Convert K8s pod to our PodStatus model"""
        restart_count = 0
        if pod.status.container_statuses:
            restart_count = sum(cs.restart_count or 0 for cs in pod.status.container_statuses)

        age = datetime.now(pod.metadata.creation_timestamp.tzinfo) - pod.metadata.creation_timestamp

        return PodStatus(
            name=pod.metadata.name,
            namespace=pod.metadata.namespace,
            status=pod.status.phase,
            restarts=restart_count,
            age=f"{age.days}d" if age.days > 0 else f"{age.seconds // 3600}h",
            node=pod.spec.node_name,
            conditions=[c.to_dict() for c in (pod.status.conditions or [])],
            container_statuses=[cs.to_dict() for cs in (pod.status.container_statuses or [])]
        )

    def _node_to_status(self, node) -> NodeStatus:
        """Convert K8s node to our NodeStatus model"""
        is_ready = False
        for condition in (node.status.conditions or []):
            if condition.type == "Ready":
                is_ready = condition.status == "True"
                break

        age = datetime.now(node.metadata.creation_timestamp.tzinfo) - node.metadata.creation_timestamp

        return NodeStatus(
            name=node.metadata.name,
            status="Ready" if is_ready else "NotReady",
            roles=list(node.metadata.labels.get("kubernetes.io/role", "").split(",")),
            age=f"{age.days}d",
            version=node.status.node_info.kubelet_version,
            conditions=[c.to_dict() for c in (node.status.conditions or [])]
        )
