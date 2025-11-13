"""
Investigation Orchestrator

Coordinates the entire investigation workflow:
1. Collect data from sources
2. Correlate events
3. AI analysis for root cause
4. Generate recommendations
5. Save to knowledge base
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime

from .collectors import K8sCollector
from .analyzers import EventCorrelator, RootCauseAnalyzer
from .models import (
    Investigation,
    Event,
    Correlation,
    RootCauseAnalysis,
    Action
)

logger = logging.getLogger(__name__)


class Investigator:
    """
    Main orchestrator for incident investigations

    Implements the multi-agent pattern:
    - Data collectors run in parallel
    - Correlator finds relationships
    - AI analyzer provides root cause
    - Action generator suggests remediation
    """

    def __init__(self):
        """Initialize investigator with collectors and analyzers"""
        # Collectors
        self.k8s_collector = K8sCollector()

        # Analyzers
        self.correlator = EventCorrelator()
        self.root_cause_analyzer = RootCauseAnalyzer()

        logger.info("Investigator initialized")

    async def investigate(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> Investigation:
        """
        Perform a complete investigation

        Args:
            query: User's investigation query (e.g., "API is slow")
            user_id: User who initiated the investigation

        Returns:
            Investigation with findings and recommendations
        """
        logger.info(f"Starting investigation: '{query}' (user: {user_id})")

        investigation = Investigation(
            query=query,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            status="in_progress"
        )

        try:
            # Step 1: Collect data from all sources (parallel)
            logger.info("Step 1: Collecting data...")
            events = await self._collect_data(query)
            investigation.events = events

            if not events:
                logger.warning("No events collected")
                investigation.status = "completed"
                return investigation

            logger.info(f"Collected {len(events)} events")

            # Step 2: Correlate events
            logger.info("Step 2: Correlating events...")
            correlations = self.correlator.correlate(events)
            investigation.correlations = correlations

            logger.info(f"Found {len(correlations)} correlations")

            # Step 3: AI root cause analysis
            logger.info("Step 3: Analyzing root cause with AI...")
            analysis = await self.root_cause_analyzer.analyze(
                query=query,
                events=events,
                correlations=correlations,
                similar_past_incidents=None  # TODO: Implement RAG in Phase 3
            )
            investigation.analysis = analysis

            logger.info(f"Root cause: {analysis.root_cause} (confidence: {analysis.confidence:.0%})")

            # Step 4: Generate remediation actions
            logger.info("Step 4: Generating remediation actions...")
            actions = await self.root_cause_analyzer.generate_remediation_actions(
                root_cause_analysis=analysis,
                events=events
            )
            investigation.recommended_actions = actions

            logger.info(f"Generated {len(actions)} recommended actions")

            # Mark as completed
            investigation.status = "completed"

            # TODO: Phase 3 - Save to knowledge base for learning
            # await self._save_to_knowledge_base(investigation)

            logger.info(f"Investigation completed successfully: {investigation.id}")

            return investigation

        except Exception as e:
            logger.error(f"Investigation failed: {e}", exc_info=True)
            investigation.status = "failed"
            investigation.resolution = f"Investigation failed: {str(e)}"
            return investigation

    async def _collect_data(self, query: str) -> List[Event]:
        """
        Collect data from all sources in parallel

        Args:
            query: Investigation query (may contain filters)

        Returns:
            List of all collected events
        """
        # Run collectors in parallel
        results = await asyncio.gather(
            self.k8s_collector.collect(query),
            # TODO: Add more collectors in Phase 2
            # self.log_collector.collect(query),
            # self.metrics_collector.collect(query),
            return_exceptions=True
        )

        # Merge events from all successful collectors
        all_events: List[Event] = []

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Collector failed: {result}")
                continue

            if result.success:
                all_events.extend(result.events)
            else:
                logger.warning(f"Collector '{result.collector_name}' failed: {result.error}")

        return all_events

    async def get_cluster_health(self):
        """
        Get overall cluster health (quick check without full investigation)

        Returns:
            K8sClusterHealth summary
        """
        return await self.k8s_collector.get_cluster_health()

    async def run_diagnostics(self) -> dict:
        """
        Run diagnostic checks on all components

        Returns:
            Dict with health status of each component
        """
        diagnostics = {
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }

        # Check K8s collector
        try:
            k8s_healthy = await self.k8s_collector.health_check()
            diagnostics["components"]["k8s_collector"] = {
                "status": "healthy" if k8s_healthy else "unhealthy",
                "healthy": k8s_healthy
            }
        except Exception as e:
            diagnostics["components"]["k8s_collector"] = {
                "status": "error",
                "error": str(e),
                "healthy": False
            }

        # TODO: Check other collectors when added

        # Check AI analyzer
        try:
            # Simple check - can we initialize the client?
            _ = self.root_cause_analyzer.client
            diagnostics["components"]["ai_analyzer"] = {
                "status": "healthy",
                "healthy": True
            }
        except Exception as e:
            diagnostics["components"]["ai_analyzer"] = {
                "status": "error",
                "error": str(e),
                "healthy": False
            }

        # Overall health
        all_healthy = all(
            comp.get("healthy", False)
            for comp in diagnostics["components"].values()
        )

        diagnostics["overall_status"] = "healthy" if all_healthy else "degraded"

        return diagnostics
