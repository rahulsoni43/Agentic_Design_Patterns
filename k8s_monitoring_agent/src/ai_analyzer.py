#!/usr/bin/env python3
"""
AI-Powered Cluster Health Analyzer

Uses Claude AI to:
1. Detect anomalies in cluster health data
2. Predict potential issues before outages
3. Provide root cause analysis
4. Generate remediation recommendations

Patterns used:
- Tool Use (Chapter 5): Analyze K8s data
- Reflection (Chapter 4): Validate recommendations
- Planning (Chapter 6): Create action plans
"""

import os
import json
from typing import Dict, Any, List
from anthropic import Anthropic
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIAnalyzer:
    """
    AI-powered analyzer for Kubernetes cluster health
    """

    def __init__(self, api_key=None):
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-5-20250929"

    def _call_claude(self, prompt: str, max_tokens=4096) -> str:
        """Call Claude API"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"AI API call failed: {e}")
            return f"Error: {str(e)}"

    def analyze_cluster_health(self, cluster_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive AI analysis of cluster health

        Returns:
            {
                "severity": "CRITICAL" | "WARNING" | "INFO" | "OK",
                "issues_found": [...],
                "predictions": [...],
                "recommendations": [...],
                "should_alert": bool
            }
        """
        logger.info("Starting AI analysis of cluster health...")

        # Step 1: Detect current issues
        issues = self._detect_issues(cluster_data)

        # Step 2: Predict future problems
        predictions = self._predict_issues(cluster_data, issues)

        # Step 3: Generate recommendations
        recommendations = self._generate_recommendations(cluster_data, issues, predictions)

        # Step 4: Determine severity and alert necessity
        severity = self._determine_severity(issues, predictions)

        analysis = {
            "timestamp": cluster_data.get("timestamp"),
            "severity": severity,
            "issues_found": issues,
            "predictions": predictions,
            "recommendations": recommendations,
            "should_alert": severity in ["CRITICAL", "WARNING"],
            "cluster_summary": self._summarize_cluster(cluster_data)
        }

        logger.info(f"Analysis complete. Severity: {severity}, Should Alert: {analysis['should_alert']}")

        return analysis

    def _detect_issues(self, cluster_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Use AI to detect current issues in the cluster
        """
        prompt = f"""
You are an expert SRE analyzing Kubernetes cluster health data.

Analyze this cluster snapshot and identify ALL issues, problems, and anomalies.

Cluster Data:
{json.dumps(cluster_data, indent=2)}

For each issue found, provide:
1. Issue type (CrashLoop, NodePressure, HighRestarts, ResourceExhaustion, etc.)
2. Severity (CRITICAL, HIGH, MEDIUM, LOW)
3. Affected resources (namespace/name)
4. Root cause analysis
5. User impact (none, degraded, outage)
6. Time to failure (if trending toward outage)

Return a JSON array of issues:
[
  {{
    "type": "CrashLoopBackOff",
    "severity": "CRITICAL",
    "resource": "production/api-server-abc123",
    "root_cause": "OOMKilled - container exceeding memory limit",
    "impact": "degraded",
    "time_to_failure": "5-10 minutes",
    "details": "Pod restarted 15 times in 10 minutes. Memory usage at 99%."
  }}
]

If no issues found, return empty array: []

ONLY return valid JSON, no other text.
"""

        response = self._call_claude(prompt)

        try:
            # Parse JSON from response
            issues = json.loads(response)
            return issues
        except json.JSONDecodeError:
            logger.error("Failed to parse AI response as JSON")
            # Try to extract JSON from markdown code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                try:
                    return json.loads(json_str)
                except:
                    pass
            return []

    def _predict_issues(self, cluster_data: Dict[str, Any], current_issues: List[Dict]) -> List[Dict[str, Any]]:
        """
        Use AI to predict future issues based on trends
        """
        prompt = f"""
You are an expert SRE doing predictive analysis on a Kubernetes cluster.

Current Cluster State:
{json.dumps(cluster_data, indent=2)}

Current Issues:
{json.dumps(current_issues, indent=2)}

Analyze trends and patterns to predict problems BEFORE they cause outages.

Look for:
1. Resource usage trending upward (will hit limits soon)
2. Error rate increases (small now, will compound)
3. Event patterns (spike in restarts, image pulls, etc.)
4. Cascading failures (one issue will trigger others)
5. Capacity issues (node resources filling up)

For each prediction, provide:
1. What will happen
2. When it will happen (timeframe)
3. Confidence level (high, medium, low)
4. What will trigger it
5. Impact if not addressed

Return JSON array:
[
  {{
    "prediction": "Node will run out of memory",
    "timeframe": "15-30 minutes",
    "confidence": "high",
    "trigger": "Memory usage increasing 5% per 10 minutes",
    "impact": "Pod evictions, service degradation",
    "probability": 0.85
  }}
]

If no predictions, return: []

ONLY return valid JSON.
"""

        response = self._call_claude(prompt)

        try:
            predictions = json.loads(response)
            return predictions
        except json.JSONDecodeError:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                try:
                    return json.loads(json_str)
                except:
                    pass
            return []

    def _generate_recommendations(
        self,
        cluster_data: Dict[str, Any],
        issues: List[Dict],
        predictions: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations with kubectl commands
        """
        prompt = f"""
You are an expert SRE providing remediation guidance.

Cluster Data:
{json.dumps(cluster_data, indent=2)}

Issues Found:
{json.dumps(issues, indent=2)}

Predictions:
{json.dumps(predictions, indent=2)}

Generate specific, actionable recommendations to fix current issues and prevent predicted ones.

For each recommendation:
1. What action to take
2. Priority (P0-immediate, P1-urgent, P2-soon, P3-when-possible)
3. Actual kubectl commands to run
4. Expected outcome
5. Risk level (low, medium, high)
6. Verification steps

Return JSON array:
[
  {{
    "action": "Increase memory limit for api-server",
    "priority": "P0",
    "commands": [
      "kubectl set resources deployment api-server -n production --limits=memory=1Gi",
      "kubectl rollout status deployment api-server -n production"
    ],
    "outcome": "Prevent OOMKill, stabilize pod",
    "risk": "low",
    "verify": "kubectl get pods -n production | grep api-server"
  }}
]

Prioritize actions that:
- Prevent outages (not just fix symptoms)
- Are safe to run in production
- Provide immediate value

If no actions needed, return: []

ONLY return valid JSON.
"""

        response = self._call_claude(prompt)

        try:
            recommendations = json.loads(response)
            return recommendations
        except json.JSONDecodeError:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                try:
                    return json.loads(json_str)
                except:
                    pass
            return []

    def _determine_severity(self, issues: List[Dict], predictions: List[Dict]) -> str:
        """
        Determine overall severity level
        """
        # Count critical/high issues
        critical_issues = sum(1 for i in issues if i.get("severity") == "CRITICAL")
        high_issues = sum(1 for i in issues if i.get("severity") == "HIGH")

        # Check predictions
        high_confidence_predictions = sum(1 for p in predictions if p.get("confidence") == "high")

        # Determine severity
        if critical_issues > 0:
            return "CRITICAL"
        elif high_issues > 0 or high_confidence_predictions > 0:
            return "WARNING"
        elif len(issues) > 0 or len(predictions) > 0:
            return "INFO"
        else:
            return "OK"

    def _summarize_cluster(self, cluster_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a quick summary of cluster state
        """
        pods = cluster_data.get("pods", {})
        nodes = cluster_data.get("nodes", {})

        return {
            "total_pods": pods.get("total_pods", 0),
            "total_nodes": nodes.get("total_nodes", 0),
            "pods_with_issues": pods.get("issues", 0),
            "nodes_ready": nodes.get("ready", 0),
            "nodes_not_ready": nodes.get("not_ready", 0),
        }

    def format_for_slack(self, analysis: Dict[str, Any]) -> str:
        """
        Format analysis results for Slack notification
        """
        severity = analysis["severity"]
        emoji = {"CRITICAL": "🔴", "WARNING": "🟠", "INFO": "🟡", "OK": "🟢"}.get(severity, "⚪")

        # Build Slack message
        message = f"{emoji} *{severity}*: Kubernetes Cluster Health Alert\n\n"

        # Issues
        if analysis["issues_found"]:
            message += "*Issues Detected:*\n"
            for issue in analysis["issues_found"][:5]:  # Limit to 5
                message += f"• *{issue.get('type')}* - {issue.get('resource')}\n"
                message += f"  ↳ {issue.get('details', 'No details')}\n"
                message += f"  ↳ Impact: {issue.get('impact', 'unknown')}\n"
            if len(analysis["issues_found"]) > 5:
                message += f"  _...and {len(analysis['issues_found']) - 5} more issues_\n"
            message += "\n"

        # Predictions
        if analysis["predictions"]:
            message += "*Predictions:*\n"
            for pred in analysis["predictions"][:3]:
                message += f"• {pred.get('prediction')} (in {pred.get('timeframe')})\n"
                message += f"  ↳ Confidence: {pred.get('confidence')}\n"
            message += "\n"

        # Recommendations
        if analysis["recommendations"]:
            message += "*Recommended Actions:*\n"
            for i, rec in enumerate(analysis["recommendations"][:3], 1):
                message += f"{i}. *{rec.get('action')}* (Priority: {rec.get('priority')})\n"
                if rec.get('commands'):
                    message += f"   ```{rec['commands'][0]}```\n"
            message += "\n"

        # Cluster summary
        summary = analysis.get("cluster_summary", {})
        message += f"*Cluster Status:*\n"
        message += f"Pods: {summary.get('total_pods', 0)} ({summary.get('pods_with_issues', 0)} issues)\n"
        message += f"Nodes: {summary.get('nodes_ready', 0)}/{summary.get('total_nodes', 0)} ready\n"

        return message


# Example usage
if __name__ == "__main__":
    # Sample cluster data (from k8s_collector.py)
    sample_data = {
        "timestamp": "2025-01-13T10:30:00",
        "pods": {
            "total_pods": 50,
            "issues": 3,
            "crashlooping": [
                {
                    "name": "api-server-abc123",
                    "namespace": "production",
                    "reason": "CrashLoopBackOff",
                    "restarts": 15,
                    "container": "api"
                }
            ],
            "high_restarts": [],
            "pending": [],
            "failed": []
        },
        "nodes": {
            "total_nodes": 3,
            "ready": 3,
            "not_ready": 0,
            "issues": [],
            "pressure": []
        },
        "events": {
            "warnings": [
                {"reason": "BackOff", "message": "Back-off restarting failed container"}
            ],
            "errors": [],
            "event_storm": False
        }
    }

    # Analyze
    analyzer = AIAnalyzer()
    analysis = analyzer.analyze_cluster_health(sample_data)

    print("\n" + "=" * 70)
    print("AI CLUSTER ANALYSIS")
    print("=" * 70 + "\n")

    print(f"Severity: {analysis['severity']}")
    print(f"Should Alert: {analysis['should_alert']}\n")

    print(f"Issues Found: {len(analysis['issues_found'])}")
    print(f"Predictions: {len(analysis['predictions'])}")
    print(f"Recommendations: {len(analysis['recommendations'])}\n")

    # Show Slack formatted message
    print("SLACK MESSAGE:")
    print("-" * 70)
    print(analyzer.format_for_slack(analysis))
    print("-" * 70)
