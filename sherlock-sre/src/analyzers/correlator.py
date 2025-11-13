"""
Event Correlator

Correlates events from multiple sources to find relationships.
Uses temporal, causal, and semantic correlation.
"""

from typing import List
from datetime import timedelta
import logging

from ..models import Event, Correlation, EventType

logger = logging.getLogger(__name__)


class EventCorrelator:
    """
    Correlates events to find relationships

    Correlation types:
    1. Temporal: Events close in time (within ±5 minutes)
    2. Causal: Events where one likely caused another
    3. Semantic: Events with similar error messages/patterns
    """

    def __init__(self, temporal_window_seconds: int = 300):
        """
        Args:
            temporal_window_seconds: Time window for temporal correlation (default: 5 min)
        """
        self.temporal_window = timedelta(seconds=temporal_window_seconds)

    def correlate(self, events: List[Event]) -> List[Correlation]:
        """
        Find correlations between events

        Args:
            events: List of events to correlate

        Returns:
            List of correlations found
        """
        correlations: List[Correlation] = []

        if len(events) < 2:
            return correlations

        # Sort by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Find temporal correlations
        temporal_corrs = self._find_temporal_correlations(sorted_events)
        correlations.extend(temporal_corrs)

        # Find causal correlations
        causal_corrs = self._find_causal_correlations(sorted_events)
        correlations.extend(causal_corrs)

        # Deduplicate
        correlations = self._deduplicate_correlations(correlations)

        return correlations

    def _find_temporal_correlations(self, events: List[Event]) -> List[Correlation]:
        """
        Find events that happened close in time

        Strategy: Group events that occurred within the temporal window
        """
        correlations: List[Correlation] = []

        for i, event1 in enumerate(events):
            related_events = [event1]

            for j, event2 in enumerate(events[i + 1:], start=i + 1):
                time_diff = abs((event2.timestamp - event1.timestamp).total_seconds())

                if time_diff <= self.temporal_window.total_seconds():
                    related_events.append(event2)
                else:
                    # Events are sorted, so no point checking further
                    break

            # Create correlation if we found related events
            if len(related_events) > 1:
                correlations.append(Correlation(
                    events=related_events,
                    correlation_type="temporal",
                    confidence=0.7,  # Moderate confidence for temporal
                    reasoning=f"Events occurred within {self.temporal_window.total_seconds()}s of each other"
                ))

        return correlations

    def _find_causal_correlations(self, events: List[Event]) -> List[Correlation]:
        """
        Find events where one likely caused another

        Causal patterns:
        - Pod crash → OOMKilled (memory exhaustion caused crash)
        - Node pressure → Pod pending (resource pressure preventing scheduling)
        - Deployment failure → Pod crash (bad deploy caused crashes)
        - Error spike → Latency spike (errors slow down system)
        """
        correlations: List[Correlation] = []

        # Define causal relationships
        causal_patterns = [
            (EventType.HIGH_MEMORY, EventType.POD_CRASH, "Memory exhaustion likely caused pod crash"),
            (EventType.NODE_PRESSURE, EventType.POD_CRASH, "Node pressure likely caused pod issues"),
            (EventType.DEPLOYMENT_FAILURE, EventType.POD_CRASH, "Deployment failure likely caused crashes"),
            (EventType.ERROR_SPIKE, EventType.LATENCY_SPIKE, "Error spike likely caused latency increase"),
            (EventType.HIGH_CPU, EventType.LATENCY_SPIKE, "High CPU likely caused slow responses"),
        ]

        for cause_type, effect_type, reasoning in causal_patterns:
            # Find cause events
            cause_events = [e for e in events if e.event_type == cause_type]

            # Find effect events
            effect_events = [e for e in events if e.event_type == effect_type]

            # Match cause → effect if effect happened shortly after cause
            for cause in cause_events:
                for effect in effect_events:
                    time_diff = (effect.timestamp - cause.timestamp).total_seconds()

                    # Effect should happen after cause, within temporal window
                    if 0 < time_diff <= self.temporal_window.total_seconds():
                        # Check if same resource or related
                        if self._are_resources_related(cause.resource, effect.resource):
                            correlations.append(Correlation(
                                events=[cause, effect],
                                correlation_type="causal",
                                confidence=0.85,  # High confidence for causal
                                reasoning=reasoning
                            ))

        return correlations

    def _are_resources_related(self, resource1: str, resource2: str) -> bool:
        """
        Check if two resources are related

        Examples:
        - Same pod: "production/api-server-abc" == "production/api-server-abc"
        - Same deployment: "production/api-server-*" related
        - Same namespace: "production/*" related
        """
        # Exact match
        if resource1 == resource2:
            return True

        # Same namespace
        ns1 = resource1.split("/")[0] if "/" in resource1 else ""
        ns2 = resource2.split("/")[0] if "/" in resource2 else ""

        if ns1 and ns2 and ns1 == ns2:
            # Check if same deployment (pod name pattern)
            name1 = resource1.split("/")[1] if "/" in resource1 else resource1
            name2 = resource2.split("/")[1] if "/" in resource2 else resource2

            # Strip pod hash suffix (e.g., api-server-abc123-xyz becomes api-server)
            base1 = "-".join(name1.split("-")[:-2]) if len(name1.split("-")) > 2 else name1
            base2 = "-".join(name2.split("-")[:-2]) if len(name2.split("-")) > 2 else name2

            if base1 == base2:
                return True

        return False

    def _deduplicate_correlations(self, correlations: List[Correlation]) -> List[Correlation]:
        """
        Remove duplicate correlations

        Two correlations are duplicates if they involve the same set of events
        """
        seen = set()
        unique = []

        for corr in correlations:
            # Create a unique key from event IDs
            event_ids = tuple(sorted(str(e.id) for e in corr.events))

            if event_ids not in seen:
                seen.add(event_ids)
                unique.append(corr)

        return unique

    def get_correlation_summary(self, correlations: List[Correlation]) -> dict:
        """
        Get a summary of correlations

        Returns:
            Dict with correlation statistics
        """
        if not correlations:
            return {
                "total": 0,
                "by_type": {},
                "average_confidence": 0.0
            }

        by_type = {}
        for corr in correlations:
            by_type[corr.correlation_type] = by_type.get(corr.correlation_type, 0) + 1

        avg_confidence = sum(c.confidence for c in correlations) / len(correlations)

        return {
            "total": len(correlations),
            "by_type": by_type,
            "average_confidence": round(avg_confidence, 2)
        }
