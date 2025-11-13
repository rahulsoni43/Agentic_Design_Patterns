"""
CLI Interface for Sherlock SRE

Command-line tool for testing and investigations without Slack.
Useful for development and debugging.
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime

from .investigator import Investigator
from .config import settings


def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    # Quiet third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("kubernetes").setLevel(logging.WARNING)


async def investigate_command(args):
    """Run an investigation"""
    print("=" * 70)
    print("SHERLOCK SRE - INVESTIGATION")
    print("=" * 70)
    print(f"Query: {args.query}")
    print(f"Time: {datetime.now()}")
    print("=" * 70)
    print()

    investigator = Investigator()

    print("🔍 Starting investigation...")
    print()

    investigation = await investigator.investigate(
        query=args.query,
        user_id="cli"
    )

    print("=" * 70)
    print("INVESTIGATION RESULTS")
    print("=" * 70)
    print()

    # Events
    print(f"📊 Events Detected: {len(investigation.events)}")
    if investigation.events:
        events_by_type = {}
        for event in investigation.events:
            events_by_type[event.event_type.value] = events_by_type.get(event.event_type.value, 0) + 1

        for event_type, count in sorted(events_by_type.items(), key=lambda x: -x[1]):
            print(f"  • {count}x {event_type.replace('_', ' ').title()}")

    print()

    # Correlations
    print(f"🔗 Correlations Found: {len(investigation.correlations)}")
    if investigation.correlations:
        for i, corr in enumerate(investigation.correlations[:5], 1):
            print(f"  {i}. {corr.correlation_type.upper()}: {corr.reasoning}")

    print()

    # Root cause
    if investigation.analysis:
        print("🎯 Root Cause Analysis")
        print(f"  {investigation.analysis.root_cause}")
        print(f"  Confidence: {investigation.analysis.confidence:.0%}")
        print()

        if investigation.analysis.evidence:
            print("  Evidence:")
            for evidence in investigation.analysis.evidence:
                print(f"    • {evidence}")
            print()

        if investigation.analysis.alternative_causes:
            print("  Alternative Causes:")
            for alt in investigation.analysis.alternative_causes:
                print(f"    • {alt}")
            print()

    # Actions
    if investigation.recommended_actions:
        print("🔧 Recommended Actions")
        for i, action in enumerate(investigation.recommended_actions, 1):
            print(f"\n  {i}. {action.description}")
            print(f"     Risk: {action.risk_level.upper()}")
            if action.command:
                print(f"     Command: {action.command}")
            print(f"     Expected: {action.expected_outcome}")

    print()
    print("=" * 70)

    # JSON output if requested
    if args.json:
        output_file = args.json
        with open(output_file, 'w') as f:
            json.dump(investigation.dict(), f, indent=2, default=str)
        print(f"Full results saved to: {output_file}")


async def health_command(args):
    """Check cluster health"""
    print("=" * 70)
    print("KUBERNETES CLUSTER HEALTH")
    print("=" * 70)
    print()

    investigator = Investigator()

    print("Checking cluster health...")
    health = await investigator.get_cluster_health()

    print(f"\n📊 Cluster Overview")
    print(f"  Nodes: {health.ready_nodes}/{health.total_nodes} ready")
    print(f"  Pods: {health.running_pods}/{health.total_pods} running")

    if health.crashlooping_pods:
        print(f"\n🔴 CrashLooping Pods: {len(health.crashlooping_pods)}")
        for pod in health.crashlooping_pods[:5]:
            print(f"  • {pod.namespace}/{pod.name} ({pod.restarts} restarts)")

    if health.failed_pods:
        print(f"\n🔴 Failed Pods: {len(health.failed_pods)}")
        for pod in health.failed_pods[:5]:
            print(f"  • {pod.namespace}/{pod.name} - {pod.status}")

    if health.pending_pods:
        print(f"\n🟡 Pending Pods: {len(health.pending_pods)}")
        for pod in health.pending_pods[:5]:
            print(f"  • {pod.namespace}/{pod.name}")

    if health.node_issues:
        print(f"\n🔴 Node Issues: {len(health.node_issues)}")
        for node in health.node_issues:
            print(f"  • {node.name} - {node.status}")

    if not (health.crashlooping_pods or health.failed_pods or health.pending_pods or health.node_issues):
        print("\n✅ No issues detected - cluster is healthy!")

    print()


async def diagnostics_command(args):
    """Run system diagnostics"""
    print("=" * 70)
    print("SHERLOCK DIAGNOSTICS")
    print("=" * 70)
    print()

    investigator = Investigator()

    print("Running diagnostics...")
    diag = await investigator.run_diagnostics()

    print(f"\nOverall Status: {diag['overall_status'].upper()}")
    print(f"Timestamp: {diag['timestamp']}")
    print("\nComponents:")

    for component, status in diag["components"].items():
        emoji = "✅" if status["healthy"] else "❌"
        print(f"  {emoji} {component}: {status['status']}")
        if "error" in status:
            print(f"      Error: {status['error']}")

    print()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Sherlock SRE - AI-Powered Incident Investigation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Investigate an issue
  sherlock investigate "API is returning 502s"

  # Check cluster health
  sherlock health

  # Run diagnostics
  sherlock diagnostics

  # Save results as JSON
  sherlock investigate "pod crashlooping" --json results.json
        """
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose logging'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Investigate command
    investigate_parser = subparsers.add_parser(
        'investigate',
        help='Investigate an issue'
    )
    investigate_parser.add_argument(
        'query',
        help='Investigation query (e.g., "API is slow")'
    )
    investigate_parser.add_argument(
        '--json',
        help='Save results to JSON file'
    )

    # Health command
    subparsers.add_parser(
        'health',
        help='Check Kubernetes cluster health'
    )

    # Diagnostics command
    subparsers.add_parser(
        'diagnostics',
        help='Run system diagnostics'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    setup_logging(args.verbose)

    # Run the appropriate command
    try:
        if args.command == 'investigate':
            asyncio.run(investigate_command(args))
        elif args.command == 'health':
            asyncio.run(health_command(args))
        elif args.command == 'diagnostics':
            asyncio.run(diagnostics_command(args))

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Command failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
