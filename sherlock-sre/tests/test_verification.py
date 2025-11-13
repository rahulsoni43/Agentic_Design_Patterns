"""
Sherlock SRE - System Verification Tests

Quick verification tests to ensure the system is working correctly.
"""

import asyncio
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_config() -> Dict[str, Any]:
    """Verify configuration is loaded correctly"""
    result = {"name": "Configuration", "status": "unknown", "details": ""}

    try:
        from src.config import settings

        # Check required fields
        if not settings.anthropic_api_key or settings.anthropic_api_key == "your-api-key-here":
            result["status"] = "failed"
            result["details"] = "ANTHROPIC_API_KEY not set in .env"
            return result

        result["status"] = "passed"
        result["details"] = f"Environment: {settings.environment}"

    except Exception as e:
        result["status"] = "failed"
        result["details"] = str(e)

    return result


async def verify_kubernetes() -> Dict[str, Any]:
    """Verify Kubernetes connection"""
    result = {"name": "Kubernetes Connection", "status": "unknown", "details": ""}

    try:
        from src.collectors.k8s_collector import KubernetesCollector

        collector = KubernetesCollector()

        # Try to list namespaces (simple check)
        from kubernetes import client
        v1 = client.CoreV1Api()
        namespaces = v1.list_namespace(timeout_seconds=5)

        result["status"] = "passed"
        result["details"] = f"Connected to cluster with {len(namespaces.items)} namespaces"

    except Exception as e:
        result["status"] = "warning"
        result["details"] = f"Cannot connect to Kubernetes: {str(e)}"

    return result


async def verify_ai_client() -> Dict[str, Any]:
    """Verify AI client can connect"""
    result = {"name": "AI Client (Anthropic)", "status": "unknown", "details": ""}

    try:
        from anthropic import Anthropic
        from src.config import settings

        client = Anthropic(api_key=settings.anthropic_api_key)

        # Simple test call
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=50,
            messages=[{"role": "user", "content": "Reply with just 'OK'"}]
        )

        result["status"] = "passed"
        result["details"] = "Successfully connected to Claude API"

    except Exception as e:
        result["status"] = "failed"
        result["details"] = str(e)

    return result


async def verify_models() -> Dict[str, Any]:
    """Verify data models are importable"""
    result = {"name": "Data Models", "status": "unknown", "details": ""}

    try:
        from src.models import (
            Event, EventType, Severity,
            Correlation, CorrelationType,
            RootCauseAnalysis, Investigation,
            Action, ActionType
        )

        # Test creating a simple event
        event = Event(
            event_type=EventType.POD_CRASH,
            source="test",
            severity=Severity.HIGH,
            message="Test event",
            resource="test-pod",
            namespace="default"
        )

        result["status"] = "passed"
        result["details"] = "All models imported successfully"

    except Exception as e:
        result["status"] = "failed"
        result["details"] = str(e)

    return result


async def verify_collectors() -> Dict[str, Any]:
    """Verify collectors can be initialized"""
    result = {"name": "Data Collectors", "status": "unknown", "details": ""}

    try:
        from src.collectors.k8s_collector import KubernetesCollector

        collector = KubernetesCollector()

        result["status"] = "passed"
        result["details"] = "Kubernetes collector initialized"

    except Exception as e:
        result["status"] = "failed"
        result["details"] = str(e)

    return result


async def verify_analyzers() -> Dict[str, Any]:
    """Verify analyzers can be initialized"""
    result = {"name": "Analyzers", "status": "unknown", "details": ""}

    try:
        from src.analyzers.correlator import EventCorrelator
        from src.analyzers.root_cause_analyzer import RootCauseAnalyzer

        correlator = EventCorrelator()
        analyzer = RootCauseAnalyzer()

        result["status"] = "passed"
        result["details"] = "Event correlator and root cause analyzer initialized"

    except Exception as e:
        result["status"] = "failed"
        result["details"] = str(e)

    return result


async def verify_investigator() -> Dict[str, Any]:
    """Verify main investigator can be initialized"""
    result = {"name": "Main Investigator", "status": "unknown", "details": ""}

    try:
        from src.investigator import Investigator

        investigator = Investigator()

        result["status"] = "passed"
        result["details"] = "Main investigator initialized successfully"

    except Exception as e:
        result["status"] = "failed"
        result["details"] = str(e)

    return result


async def verify_slack_bot() -> Dict[str, Any]:
    """Verify Slack bot can be initialized (if configured)"""
    result = {"name": "Slack Bot", "status": "unknown", "details": ""}

    try:
        from src.config import settings

        if not settings.slack_bot_token:
            result["status"] = "skipped"
            result["details"] = "Slack tokens not configured (optional)"
            return result

        from src.interfaces.slack_bot import SherlockSlackBot
        from src.investigator import Investigator

        investigator = Investigator()
        slack_bot = SherlockSlackBot(investigator)

        result["status"] = "passed"
        result["details"] = "Slack bot initialized successfully"

    except Exception as e:
        result["status"] = "warning"
        result["details"] = f"Slack bot initialization issue: {str(e)}"

    return result


async def run_all_verifications():
    """Run all verification tests"""

    print("=" * 70)
    print(" Sherlock SRE - System Verification")
    print("=" * 70)
    print()

    verifications = [
        verify_config(),
        verify_models(),
        verify_collectors(),
        verify_analyzers(),
        verify_investigator(),
        verify_kubernetes(),
        verify_ai_client(),
        verify_slack_bot(),
    ]

    results = await asyncio.gather(*verifications, return_exceptions=True)

    passed = 0
    failed = 0
    warnings = 0
    skipped = 0

    for result in results:
        if isinstance(result, Exception):
            print(f"❌ EXCEPTION: {result}")
            failed += 1
            continue

        status_emoji = {
            "passed": "✅",
            "failed": "❌",
            "warning": "⚠️ ",
            "skipped": "⏭️ ",
            "unknown": "❓"
        }.get(result["status"], "❓")

        print(f"{status_emoji} {result['name']}")
        print(f"   {result['details']}")
        print()

        if result["status"] == "passed":
            passed += 1
        elif result["status"] == "failed":
            failed += 1
        elif result["status"] == "warning":
            warnings += 1
        elif result["status"] == "skipped":
            skipped += 1

    print("=" * 70)
    print(f" Summary: {passed} passed, {failed} failed, {warnings} warnings, {skipped} skipped")
    print("=" * 70)
    print()

    if failed > 0:
        print("❌ Some critical tests failed. Check your configuration.")
        print()
        print("Common fixes:")
        print("  1. Ensure .env file exists with ANTHROPIC_API_KEY")
        print("  2. Check kubectl is installed and configured")
        print("  3. Verify all dependencies are installed: pip install -r requirements.txt")
        print()
        return False
    elif warnings > 0:
        print("⚠️  All critical components passed, but some optional features have issues.")
        print("   You can still use Sherlock with reduced functionality.")
        print()
        return True
    else:
        print("✅ All verifications passed! Sherlock is ready to use.")
        print()
        print("Next steps:")
        print("  • Try: python -m src.cli health")
        print("  • Try: python -m src.cli investigate 'test issue'")
        print("  • Or start Slack bot: python -m src.main")
        print()
        return True


if __name__ == "__main__":
    asyncio.run(run_all_verifications())
