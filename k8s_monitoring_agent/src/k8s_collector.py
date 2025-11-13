#!/usr/bin/env python3
"""
Kubernetes Data Collector

Collects health data from K8s cluster using kubectl or Python client.
Uses Multi-Agent pattern (Chapter 7) with parallel data collection.
"""

import json
import subprocess
from typing import Dict, List, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class K8sCollector:
    """
    Collects data from Kubernetes cluster
    """

    def __init__(self, use_kubectl=True):
        """
        Args:
            use_kubectl: If True, use kubectl CLI. If False, use Python client.
        """
        self.use_kubectl = use_kubectl

    def _run_kubectl(self, command: str) -> Dict[str, Any]:
        """
        Execute kubectl command and return JSON output
        """
        try:
            cmd = f"kubectl {command} -o json"
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"kubectl command failed: {result.stderr}")
                return {"error": result.stderr}

            return json.loads(result.stdout)

        except subprocess.TimeoutExpired:
            logger.error(f"kubectl command timed out: {command}")
            return {"error": "Command timeout"}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse kubectl output: {e}")
            return {"error": "JSON parse error"}
        except Exception as e:
            logger.error(f"kubectl command error: {e}")
            return {"error": str(e)}

    def collect_pods(self) -> Dict[str, Any]:
        """
        Collect pod health data across all namespaces
        """
        logger.info("Collecting pod data...")

        pods_data = self._run_kubectl("get pods --all-namespaces")

        if "error" in pods_data:
            return {"error": pods_data["error"], "pods": []}

        # Analyze pods
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_pods": len(pods_data.get("items", [])),
            "by_status": {},
            "issues": [],
            "crashlooping": [],
            "pending": [],
            "failed": [],
            "high_restarts": [],
        }

        for pod in pods_data.get("items", []):
            metadata = pod.get("metadata", {})
            status = pod.get("status", {})

            pod_name = metadata.get("name", "unknown")
            namespace = metadata.get("namespace", "unknown")
            phase = status.get("phase", "Unknown")

            # Count by status
            analysis["by_status"][phase] = analysis["by_status"].get(phase, 0) + 1

            # Check for issues
            container_statuses = status.get("containerStatuses", [])

            for container in container_statuses:
                restart_count = container.get("restartCount", 0)
                state = container.get("state", {})

                # CrashLoopBackOff detection
                if "waiting" in state:
                    reason = state["waiting"].get("reason", "")
                    if "CrashLoopBackOff" in reason or "Error" in reason:
                        analysis["crashlooping"].append({
                            "name": pod_name,
                            "namespace": namespace,
                            "reason": reason,
                            "restarts": restart_count,
                            "container": container.get("name", "unknown")
                        })

                # High restart count
                if restart_count > 5:
                    analysis["high_restarts"].append({
                        "name": pod_name,
                        "namespace": namespace,
                        "restarts": restart_count,
                        "container": container.get("name", "unknown")
                    })

            # Pending pods
            if phase == "Pending":
                analysis["pending"].append({
                    "name": pod_name,
                    "namespace": namespace,
                    "conditions": status.get("conditions", [])
                })

            # Failed pods
            if phase == "Failed":
                analysis["failed"].append({
                    "name": pod_name,
                    "namespace": namespace,
                    "reason": status.get("reason", "Unknown")
                })

        # Count total issues
        analysis["issues"] = (
            len(analysis["crashlooping"]) +
            len(analysis["pending"]) +
            len(analysis["failed"]) +
            len(analysis["high_restarts"])
        )

        return analysis

    def collect_nodes(self) -> Dict[str, Any]:
        """
        Collect node health data
        """
        logger.info("Collecting node data...")

        nodes_data = self._run_kubectl("get nodes")

        if "error" in nodes_data:
            return {"error": nodes_data["error"], "nodes": []}

        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_nodes": len(nodes_data.get("items", [])),
            "ready": 0,
            "not_ready": 0,
            "issues": [],
            "pressure": [],
        }

        for node in nodes_data.get("items", []):
            metadata = node.get("metadata", {})
            status = node.get("status", {})

            node_name = metadata.get("name", "unknown")
            conditions = status.get("conditions", [])

            # Check node ready status
            for condition in conditions:
                if condition.get("type") == "Ready":
                    if condition.get("status") == "True":
                        analysis["ready"] += 1
                    else:
                        analysis["not_ready"] += 1
                        analysis["issues"].append({
                            "node": node_name,
                            "type": "NotReady",
                            "reason": condition.get("reason", "Unknown"),
                            "message": condition.get("message", "")
                        })

                # Check for pressure conditions
                if condition.get("type") in ["MemoryPressure", "DiskPressure", "PIDPressure"]:
                    if condition.get("status") == "True":
                        analysis["pressure"].append({
                            "node": node_name,
                            "type": condition.get("type"),
                            "message": condition.get("message", "")
                        })

            # Check taints (cordoned nodes)
            taints = node.get("spec", {}).get("taints", [])
            for taint in taints:
                if taint.get("effect") == "NoSchedule":
                    analysis["issues"].append({
                        "node": node_name,
                        "type": "Tainted",
                        "reason": taint.get("key", ""),
                        "message": taint.get("value", "")
                    })

        return analysis

    def collect_events(self, last_n_minutes=10) -> Dict[str, Any]:
        """
        Collect recent K8s events (warnings/errors)
        """
        logger.info("Collecting event data...")

        events_data = self._run_kubectl("get events --all-namespaces --sort-by='.lastTimestamp'")

        if "error" in events_data:
            return {"error": events_data["error"], "events": []}

        analysis = {
            "timestamp": datetime.now().isoformat(),
            "warnings": [],
            "errors": [],
            "event_storm": False,
        }

        recent_events = 0

        for event in events_data.get("items", []):
            event_type = event.get("type", "Normal")
            reason = event.get("reason", "")
            message = event.get("message", "")
            namespace = event.get("metadata", {}).get("namespace", "")
            involved_object = event.get("involvedObject", {})

            # Filter to recent events (simple approach - check last N items)
            recent_events += 1
            if recent_events > 100:  # Limit to last 100 events
                break

            if event_type == "Warning":
                analysis["warnings"].append({
                    "reason": reason,
                    "message": message,
                    "namespace": namespace,
                    "object": f"{involved_object.get('kind')}/{involved_object.get('name')}"
                })

            # Common error patterns
            error_keywords = ["Error", "Failed", "BackOff", "Unhealthy", "Killing"]
            if any(keyword in reason for keyword in error_keywords):
                analysis["errors"].append({
                    "reason": reason,
                    "message": message,
                    "namespace": namespace,
                    "object": f"{involved_object.get('kind')}/{involved_object.get('name')}"
                })

        # Detect event storm (too many warnings)
        if len(analysis["warnings"]) > 50:
            analysis["event_storm"] = True

        return analysis

    def collect_resource_usage(self) -> Dict[str, Any]:
        """
        Collect resource usage metrics (requires metrics-server)
        """
        logger.info("Collecting resource usage...")

        # Try to get node metrics
        node_metrics = self._run_kubectl("top nodes")
        pod_metrics = self._run_kubectl("top pods --all-namespaces")

        analysis = {
            "timestamp": datetime.now().isoformat(),
            "nodes": [],
            "high_cpu_pods": [],
            "high_memory_pods": [],
            "metrics_available": True
        }

        # Check if metrics-server is available
        if "error" in node_metrics or "error" in pod_metrics:
            analysis["metrics_available"] = False
            logger.warning("Metrics server not available - resource usage data unavailable")
            return analysis

        # Parse node metrics (simplified - in production parse the actual output)
        # For now, just note that metrics are available
        # In a real implementation, you'd parse the top output or use the API

        return analysis

    def collect_all(self) -> Dict[str, Any]:
        """
        Collect all data in parallel (Multi-Agent pattern)

        In production, use asyncio or threading for true parallelization
        """
        logger.info("Starting full cluster health collection...")

        start_time = datetime.now()

        # Collect all data
        # TODO: Make this truly parallel with asyncio/threading
        data = {
            "timestamp": start_time.isoformat(),
            "pods": self.collect_pods(),
            "nodes": self.collect_nodes(),
            "events": self.collect_events(),
            "resources": self.collect_resource_usage(),
        }

        duration = (datetime.now() - start_time).total_seconds()
        data["collection_duration_seconds"] = duration

        logger.info(f"Collection complete in {duration:.2f}s")

        return data


# Example usage
if __name__ == "__main__":
    collector = K8sCollector()

    print("\n" + "=" * 70)
    print("KUBERNETES CLUSTER HEALTH CHECK")
    print("=" * 70 + "\n")

    # Collect all data
    cluster_data = collector.collect_all()

    # Print summary
    print(f"📊 Collection Time: {cluster_data['collection_duration_seconds']:.2f}s\n")

    # Pods summary
    pods = cluster_data["pods"]
    print("🔷 PODS:")
    print(f"  Total: {pods.get('total_pods', 0)}")
    print(f"  CrashLooping: {len(pods.get('crashlooping', []))}")
    print(f"  High Restarts: {len(pods.get('high_restarts', []))}")
    print(f"  Pending: {len(pods.get('pending', []))}")
    print(f"  Failed: {len(pods.get('failed', []))}")
    print()

    # Nodes summary
    nodes = cluster_data["nodes"]
    print("🖥️  NODES:")
    print(f"  Total: {nodes.get('total_nodes', 0)}")
    print(f"  Ready: {nodes.get('ready', 0)}")
    print(f"  Not Ready: {nodes.get('not_ready', 0)}")
    print(f"  Pressure: {len(nodes.get('pressure', []))}")
    print()

    # Events summary
    events = cluster_data["events"]
    print("⚠️  EVENTS:")
    print(f"  Warnings: {len(events.get('warnings', []))}")
    print(f"  Errors: {len(events.get('errors', []))}")
    print(f"  Event Storm: {events.get('event_storm', False)}")
    print()

    # Show critical issues
    if pods.get('crashlooping'):
        print("🔴 CRASHLOOPING PODS:")
        for pod in pods['crashlooping'][:5]:  # Show first 5
            print(f"  - {pod['namespace']}/{pod['name']}: {pod['restarts']} restarts")
        print()

    if nodes.get('issues'):
        print("🔴 NODE ISSUES:")
        for issue in nodes['issues'][:5]:
            print(f"  - {issue['node']}: {issue['type']} - {issue['reason']}")
        print()

    print("=" * 70)
