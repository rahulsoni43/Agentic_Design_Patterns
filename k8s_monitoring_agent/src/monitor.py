#!/usr/bin/env python3
"""
Main Kubernetes Monitoring Agent

Continuously monitors cluster health, analyzes with AI, and sends alerts.

Usage:
    # Single run
    python monitor.py --once

    # Continuous monitoring (default: every 60 seconds)
    python monitor.py --interval 60

    # With cluster name
    python monitor.py --cluster my-prod-cluster --interval 120
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

from k8s_collector import K8sCollector
from ai_analyzer import AIAnalyzer
from slack_notifier import SlackNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class K8sMonitoringAgent:
    """
    Main monitoring agent that orchestrates collection, analysis, and alerting
    """

    def __init__(
        self,
        cluster_name="kubernetes",
        slack_webhook=None,
        anthropic_api_key=None
    ):
        self.cluster_name = cluster_name
        self.collector = K8sCollector()
        self.analyzer = AIAnalyzer(api_key=anthropic_api_key)
        self.notifier = SlackNotifier(webhook_url=slack_webhook)

        self.last_alert_time = None
        self.alert_cooldown = 300  # 5 minutes between similar alerts

        logger.info(f"Monitoring agent initialized for cluster: {cluster_name}")

    def run_health_check(self) -> dict:
        """
        Run a single health check cycle

        Returns:
            Analysis results
        """
        logger.info("=" * 70)
        logger.info(f"Starting health check for {self.cluster_name}")
        logger.info("=" * 70)

        try:
            # Step 1: Collect data from cluster
            logger.info("📊 Step 1: Collecting cluster data...")
            cluster_data = self.collector.collect_all()

            if not cluster_data:
                logger.error("Failed to collect cluster data")
                return None

            logger.info(f"✅ Collected data in {cluster_data.get('collection_duration_seconds', 0):.2f}s")

            # Step 2: AI analysis
            logger.info("🤖 Step 2: Running AI analysis...")
            analysis = self.analyzer.analyze_cluster_health(cluster_data)

            logger.info(f"✅ Analysis complete - Severity: {analysis['severity']}")

            # Step 3: Send alert if needed
            if analysis.get("should_alert"):
                logger.info("🚨 Step 3: Sending alert to Slack...")

                # Check cooldown
                if self._should_send_alert(analysis):
                    success = self.notifier.send_alert(analysis, self.cluster_name)
                    if success:
                        self.last_alert_time = time.time()
                        logger.info("✅ Alert sent successfully")
                    else:
                        logger.warning("⚠️  Failed to send alert")
                else:
                    logger.info("⏸️  Alert suppressed (cooldown period)")
            else:
                logger.info("✅ No alerts needed - cluster healthy")

            # Log summary
            self._log_summary(analysis)

            return analysis

        except Exception as e:
            logger.error(f"❌ Health check failed: {e}", exc_info=True)
            return None

    def _should_send_alert(self, analysis: dict) -> bool:
        """
        Determine if we should send an alert (avoid alert fatigue)

        Implements smart deduplication and rate limiting
        """
        # Always alert on CRITICAL
        if analysis["severity"] == "CRITICAL":
            return True

        # Check cooldown for WARNING/INFO
        if self.last_alert_time:
            elapsed = time.time() - self.last_alert_time
            if elapsed < self.alert_cooldown:
                logger.info(f"Alert cooldown active ({int(self.alert_cooldown - elapsed)}s remaining)")
                return False

        return True

    def _log_summary(self, analysis: dict):
        """
        Log a summary of the analysis
        """
        logger.info("-" * 70)
        logger.info("📋 HEALTH CHECK SUMMARY")
        logger.info("-" * 70)
        logger.info(f"Severity: {analysis['severity']}")
        logger.info(f"Issues: {len(analysis.get('issues_found', []))}")
        logger.info(f"Predictions: {len(analysis.get('predictions', []))}")
        logger.info(f"Recommendations: {len(analysis.get('recommendations', []))}")

        summary = analysis.get("cluster_summary", {})
        logger.info(f"Pods: {summary.get('total_pods', 0)} ({summary.get('pods_with_issues', 0)} issues)")
        logger.info(f"Nodes: {summary.get('nodes_ready', 0)}/{summary.get('total_nodes', 0)} ready")
        logger.info("-" * 70)

    def run_continuous(self, interval=60):
        """
        Run continuous monitoring

        Args:
            interval: Seconds between health checks
        """
        logger.info(f"🔄 Starting continuous monitoring (interval: {interval}s)")
        logger.info(f"Cluster: {self.cluster_name}")
        logger.info(f"Press Ctrl+C to stop\n")

        check_count = 0

        try:
            while True:
                check_count += 1
                logger.info(f"\n{'='*70}")
                logger.info(f"Health Check #{check_count} - {datetime.now().isoformat()}")
                logger.info(f"{'='*70}\n")

                self.run_health_check()

                logger.info(f"\n⏳ Sleeping for {interval}s...\n")
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("\n\n🛑 Monitoring stopped by user")
            logger.info(f"Total health checks performed: {check_count}")

    def test_integration(self):
        """
        Test all integrations (kubectl, AI, Slack)
        """
        logger.info("🧪 Testing K8s Monitoring Agent Integration\n")

        # Test 1: kubectl
        logger.info("Test 1: Kubernetes API Access")
        logger.info("-" * 40)
        try:
            cluster_data = self.collector.collect_all()
            if cluster_data and "error" not in str(cluster_data):
                logger.info("✅ kubectl access working")
                logger.info(f"   Pods: {cluster_data.get('pods', {}).get('total_pods', 0)}")
                logger.info(f"   Nodes: {cluster_data.get('nodes', {}).get('total_nodes', 0)}")
            else:
                logger.error("❌ kubectl access failed")
                return False
        except Exception as e:
            logger.error(f"❌ kubectl test failed: {e}")
            return False

        print()

        # Test 2: AI Analysis
        logger.info("Test 2: AI Analysis")
        logger.info("-" * 40)
        try:
            # Use the collected data
            analysis = self.analyzer.analyze_cluster_health(cluster_data)
            if analysis:
                logger.info("✅ AI analysis working")
                logger.info(f"   Severity: {analysis['severity']}")
            else:
                logger.error("❌ AI analysis failed")
                return False
        except Exception as e:
            logger.error(f"❌ AI test failed: {e}")
            return False

        print()

        # Test 3: Slack
        logger.info("Test 3: Slack Integration")
        logger.info("-" * 40)
        if self.notifier.webhook_url:
            success = self.notifier.send_test_message(self.cluster_name)
            if success:
                logger.info("✅ Slack notifications working")
            else:
                logger.error("❌ Slack test failed")
                return False
        else:
            logger.warning("⚠️  Slack webhook not configured (optional)")

        print()
        logger.info("=" * 40)
        logger.info("✅ All tests passed!")
        logger.info("=" * 40)

        return True


def main():
    parser = argparse.ArgumentParser(
        description="AI-powered Kubernetes cluster monitoring agent"
    )

    parser.add_argument(
        "--cluster",
        default=os.getenv("CLUSTER_NAME", "kubernetes"),
        help="Cluster name (default: kubernetes)"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Monitoring interval in seconds (default: 60)"
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (no continuous monitoring)"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Test integration and exit"
    )

    args = parser.parse_args()

    # Create agent
    agent = K8sMonitoringAgent(
        cluster_name=args.cluster,
        slack_webhook=os.getenv("SLACK_WEBHOOK_URL"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    # Run based on mode
    if args.test:
        agent.test_integration()
    elif args.once:
        agent.run_health_check()
    else:
        agent.run_continuous(interval=args.interval)


if __name__ == "__main__":
    main()
