#!/usr/bin/env python3
"""
Slack Notification Module

Sends rich, actionable alerts to Slack using webhooks.
Implements Human-in-the-Loop pattern (Chapter 13).
"""

import os
import json
import requests
from typing import Dict, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SlackNotifier:
    """
    Send notifications to Slack
    """

    def __init__(self, webhook_url=None):
        """
        Args:
            webhook_url: Slack webhook URL (or set SLACK_WEBHOOK_URL env var)
        """
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")

        if not self.webhook_url:
            logger.warning("No Slack webhook URL configured. Notifications will be logged only.")

    def send_alert(self, analysis: Dict[str, Any], cluster_name="kubernetes") -> bool:
        """
        Send cluster health alert to Slack

        Args:
            analysis: Analysis results from AIAnalyzer
            cluster_name: Name of the cluster being monitored

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.webhook_url:
            logger.warning("Slack webhook not configured - skipping notification")
            self._log_alert(analysis)
            return False

        # Build Slack message blocks (rich formatting)
        blocks = self._build_slack_blocks(analysis, cluster_name)

        payload = {
            "blocks": blocks,
            "text": f"{analysis['severity']}: Cluster health issue detected"  # Fallback text
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                logger.info("✅ Slack notification sent successfully")
                return True
            else:
                logger.error(f"❌ Slack notification failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to send Slack notification: {e}")
            return False

    def _build_slack_blocks(self, analysis: Dict[str, Any], cluster_name: str) -> list:
        """
        Build Slack Block Kit formatted message

        Slack Block Kit: https://api.slack.com/block-kit
        """
        severity = analysis["severity"]
        emoji = {
            "CRITICAL": ":red_circle:",
            "WARNING": ":large_orange_diamond:",
            "INFO": ":large_yellow_circle:",
            "OK": ":large_green_circle:"
        }.get(severity, ":white_circle:")

        blocks = []

        # Header
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} {severity}: {cluster_name} Health Alert"
            }
        })

        # Divider
        blocks.append({"type": "divider"})

        # Summary section
        summary = analysis.get("cluster_summary", {})
        summary_text = (
            f"*Cluster Status*\n"
            f"• Pods: {summary.get('total_pods', 0)} ({summary.get('pods_with_issues', 0)} with issues)\n"
            f"• Nodes: {summary.get('nodes_ready', 0)}/{summary.get('total_nodes', 0)} ready\n"
            f"• Time: {analysis.get('timestamp', 'N/A')}"
        )

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary_text}
        })

        # Issues section
        if analysis.get("issues_found"):
            issues_text = "*Issues Detected:*\n"
            for issue in analysis["issues_found"][:5]:  # Limit to 5
                issues_text += (
                    f"• *{issue.get('type')}* - `{issue.get('resource')}`\n"
                    f"  _{issue.get('details', 'No details')}_\n"
                    f"  Impact: {issue.get('impact', 'unknown')} | "
                    f"Severity: {issue.get('severity', 'unknown')}\n\n"
                )

            if len(analysis["issues_found"]) > 5:
                issues_text += f"_...and {len(analysis['issues_found']) - 5} more issues_\n"

            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": issues_text}
            })

        # Predictions section
        if analysis.get("predictions"):
            pred_text = "*:crystal_ball: Predictions:*\n"
            for pred in analysis["predictions"][:3]:
                pred_text += (
                    f"• {pred.get('prediction')} _(in {pred.get('timeframe')})_\n"
                    f"  Confidence: {pred.get('confidence')} | "
                    f"Impact: {pred.get('impact', 'unknown')}\n\n"
                )

            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": pred_text}
            })

        # Recommendations section
        if analysis.get("recommendations"):
            rec_text = "*:wrench: Recommended Actions:*\n"
            for i, rec in enumerate(analysis["recommendations"][:3], 1):
                rec_text += (
                    f"{i}. *{rec.get('action')}* _(Priority: {rec.get('priority')})_\n"
                )

                if rec.get('commands'):
                    # Show first command in code block
                    cmd = rec['commands'][0] if isinstance(rec['commands'], list) else rec['commands']
                    rec_text += f"```{cmd}```\n"

                rec_text += f"Risk: {rec.get('risk', 'unknown')}\n\n"

            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": rec_text}
            })

        # Divider
        blocks.append({"type": "divider"})

        # Actions (buttons)
        # Note: These require Slack app with interactive components
        # For webhook-only, we'll add links
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Monitored by K8s AI Agent | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        })

        return blocks

    def _log_alert(self, analysis: Dict[str, Any]):
        """
        Log alert to console when Slack is not configured
        """
        logger.info("=" * 70)
        logger.info("SLACK ALERT (would be sent if webhook configured)")
        logger.info("=" * 70)
        logger.info(f"Severity: {analysis['severity']}")
        logger.info(f"Issues: {len(analysis.get('issues_found', []))}")
        logger.info(f"Predictions: {len(analysis.get('predictions', []))}")
        logger.info(f"Recommendations: {len(analysis.get('recommendations', []))}")
        logger.info("=" * 70)

    def send_test_message(self, cluster_name="test-cluster") -> bool:
        """
        Send a test message to verify Slack integration
        """
        test_payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":white_check_mark: K8s Monitoring Agent - Test Message"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*Cluster:* `{cluster_name}`\n"
                            f"*Status:* Slack integration working!\n"
                            f"*Time:* {datetime.now().isoformat()}\n\n"
                            "You will receive alerts here when issues are detected."
                        )
                    }
                }
            ]
        }

        if not self.webhook_url:
            logger.error("Cannot send test message - no webhook URL configured")
            return False

        try:
            response = requests.post(
                self.webhook_url,
                json=test_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                logger.info("✅ Test message sent successfully!")
                return True
            else:
                logger.error(f"❌ Test message failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to send test message: {e}")
            return False


# Example usage
if __name__ == "__main__":
    import sys

    # Sample analysis data
    sample_analysis = {
        "timestamp": datetime.now().isoformat(),
        "severity": "WARNING",
        "should_alert": True,
        "cluster_summary": {
            "total_pods": 50,
            "total_nodes": 3,
            "pods_with_issues": 2,
            "nodes_ready": 3,
            "nodes_not_ready": 0
        },
        "issues_found": [
            {
                "type": "CrashLoopBackOff",
                "severity": "HIGH",
                "resource": "production/api-server-abc123",
                "root_cause": "OOMKilled - container exceeding memory limit",
                "impact": "degraded",
                "details": "Pod restarted 15 times in 10 minutes. Memory usage at 99%."
            }
        ],
        "predictions": [
            {
                "prediction": "Node will run out of memory",
                "timeframe": "15-30 minutes",
                "confidence": "high",
                "impact": "Pod evictions, service degradation"
            }
        ],
        "recommendations": [
            {
                "action": "Increase memory limit for api-server",
                "priority": "P0",
                "commands": [
                    "kubectl set resources deployment api-server -n production --limits=memory=1Gi"
                ],
                "risk": "low"
            }
        ]
    }

    # Test
    notifier = SlackNotifier()

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Sending test message...")
        notifier.send_test_message("demo-cluster")
    else:
        print("Sending sample alert...")
        notifier.send_alert(sample_analysis, "demo-cluster")
