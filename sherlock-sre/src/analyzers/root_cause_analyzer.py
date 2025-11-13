"""
Root Cause Analyzer

Uses Claude AI to analyze incidents and determine root causes.
Implements prompt engineering best practices for reliable analysis.
"""

import json
from typing import List, Optional
import logging

from anthropic import Anthropic

from ..models import (
    Event,
    Correlation,
    RootCauseAnalysis,
    Action,
    HistoricalIncident
)
from ..config import settings

logger = logging.getLogger(__name__)


class RootCauseAnalyzer:
    """
    AI-powered root cause analysis using Claude

    Uses Claude Sonnet 4.5 for:
    1. Analyzing correlated events
    2. Comparing to past incidents
    3. Reasoning about root causes
    4. Suggesting remediation actions
    """

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-5-20250929"

    async def analyze(
        self,
        query: str,
        events: List[Event],
        correlations: List[Correlation],
        similar_past_incidents: Optional[List[HistoricalIncident]] = None
    ) -> RootCauseAnalysis:
        """
        Perform root cause analysis

        Args:
            query: Original user query
            events: All collected events
            correlations: Event correlations
            similar_past_incidents: Similar historical incidents (if available)

        Returns:
            RootCauseAnalysis with findings and recommendations
        """
        try:
            # Build the analysis prompt
            prompt = self._build_analysis_prompt(
                query, events, correlations, similar_past_incidents
            )

            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.1,  # Low temperature for consistent analysis
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            response_text = response.content[0].text

            # Try to parse as JSON
            try:
                analysis_data = self._parse_json_response(response_text)
            except json.JSONDecodeError:
                # If not JSON, extract information from text
                analysis_data = self._parse_text_response(response_text)

            # Create RootCauseAnalysis
            return RootCauseAnalysis(
                root_cause=analysis_data.get("root_cause", "Unknown"),
                confidence=analysis_data.get("confidence", 0.5),
                evidence=analysis_data.get("evidence", []),
                alternative_causes=analysis_data.get("alternative_causes", [])
            )

        except Exception as e:
            logger.error(f"Root cause analysis failed: {e}", exc_info=True)
            return RootCauseAnalysis(
                root_cause=f"Analysis failed: {str(e)}",
                confidence=0.0,
                evidence=["Error during AI analysis"],
                alternative_causes=[]
            )

    def _build_analysis_prompt(
        self,
        query: str,
        events: List[Event],
        correlations: List[Correlation],
        similar_past_incidents: Optional[List[HistoricalIncident]]
    ) -> str:
        """
        Build the prompt for Claude

        Prompt engineering strategy:
        1. Clear role definition
        2. Structured data presentation
        3. Step-by-step reasoning request
        4. JSON output format
        """
        # Format events
        events_text = "\n".join([
            f"- [{e.timestamp}] {e.severity.upper()}: {e.message} "
            f"(Resource: {e.resource}, Source: {e.source})"
            for e in events[:20]  # Limit to prevent token overflow
        ])

        # Format correlations
        correlations_text = "\n".join([
            f"- {c.correlation_type.upper()} correlation (confidence: {c.confidence}): {c.reasoning}"
            for c in correlations
        ])

        # Format past incidents (if available)
        past_incidents_text = ""
        if similar_past_incidents:
            past_incidents_text = "\n\n# SIMILAR PAST INCIDENTS\n\n" + "\n".join([
                f"## Incident: {inc.title}\n"
                f"- Occurred: {inc.occurred_at}\n"
                f"- Root Cause: {inc.root_cause or 'Unknown'}\n"
                f"- Resolution: {inc.resolution or 'Not documented'}\n"
                f"- Similarity: {inc.similarity_score or 0:.0%}\n"
                for inc in similar_past_incidents[:3]  # Top 3 similar
            ])

        prompt = f"""You are an expert SRE analyzing a production incident in a Kubernetes environment.

# USER QUERY
"{query}"

# OBSERVED EVENTS (Last 10 minutes)
{events_text}

# EVENT CORRELATIONS
{correlations_text}
{past_incidents_text}

# YOUR TASK
Analyze the above data and determine the root cause of the incident.

Follow this reasoning process:
1. What symptoms are we seeing? (crashes, errors, resource issues, etc.)
2. What do the correlations tell us about causality?
3. Are there similar patterns from past incidents?
4. What is the most likely root cause?
5. What evidence supports this conclusion?
6. What other causes are possible?

# OUTPUT FORMAT
Provide your analysis in JSON format:

{{
  "root_cause": "Clear, specific description of the root cause",
  "confidence": 0.85,  // 0.0 to 1.0
  "evidence": [
    "Evidence point 1 from the data",
    "Evidence point 2 from the data",
    "Evidence point 3 from the data"
  ],
  "alternative_causes": [
    "Alternative explanation 1",
    "Alternative explanation 2"
  ]
}}

# GUIDELINES
- Be specific: "Pod OOMKilled due to memory leak" not "Memory issue"
- Cite evidence: Reference actual events/timestamps
- Be honest about confidence: Lower if data is ambiguous
- Consider alternatives: What else could explain the symptoms?
- Focus on proximate cause: The immediate technical reason

Provide ONLY the JSON output, no other text.
"""

        return prompt

    def _parse_json_response(self, response_text: str) -> dict:
        """
        Parse JSON response from Claude

        Handles markdown code blocks if present
        """
        # Try direct parse
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        if "```json" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0].strip()
            return json.loads(json_text)

        # Try extracting from plain code block
        if "```" in response_text:
            json_text = response_text.split("```")[1].split("```")[0].strip()
            return json.loads(json_text)

        raise json.JSONDecodeError("Could not find valid JSON in response", response_text, 0)

    def _parse_text_response(self, response_text: str) -> dict:
        """
        Fallback: Parse structured text response

        If Claude doesn't return JSON, try to extract key information
        """
        logger.warning("Claude did not return JSON, attempting text parsing")

        # Simple heuristics to extract information
        root_cause = "Unknown - see full response"
        confidence = 0.5
        evidence = []
        alternative_causes = []

        lines = response_text.split("\n")
        for line in lines:
            line_lower = line.lower()

            if "root cause:" in line_lower or "root cause is" in line_lower:
                root_cause = line.split(":")[-1].strip()

            if "confidence" in line_lower and any(char.isdigit() for char in line):
                # Try to extract number
                import re
                numbers = re.findall(r'0\.\d+|\d+%', line)
                if numbers:
                    conf_str = numbers[0].replace("%", "")
                    try:
                        confidence = float(conf_str)
                        if confidence > 1:  # Percentage
                            confidence = confidence / 100
                    except ValueError:
                        pass

            if "evidence" in line_lower:
                # Next few lines might be evidence
                evidence.append(line)

        return {
            "root_cause": root_cause,
            "confidence": confidence,
            "evidence": evidence if evidence else ["See full analysis"],
            "alternative_causes": alternative_causes,
            "full_response": response_text
        }

    async def generate_remediation_actions(
        self,
        root_cause_analysis: RootCauseAnalysis,
        events: List[Event]
    ) -> List[Action]:
        """
        Generate specific remediation actions based on root cause

        Args:
            root_cause_analysis: The root cause analysis
            events: Related events

        Returns:
            List of recommended actions with commands
        """
        try:
            prompt = f"""You are an expert SRE providing remediation steps for a Kubernetes incident.

# ROOT CAUSE
{root_cause_analysis.root_cause}

# EVIDENCE
{chr(10).join(f"- {e}" for e in root_cause_analysis.evidence)}

# TASK
Provide 3-5 specific remediation actions to resolve this incident and prevent recurrence.

For each action:
1. Description: What to do
2. Command: Actual kubectl/shell command (if applicable)
3. Risk: low/medium/high
4. Expected outcome: What should happen
5. Verification: How to verify it worked

# OUTPUT FORMAT (JSON)
[
  {{
    "description": "Restart the failing pod",
    "command": "kubectl delete pod api-server-abc123 -n production",
    "risk_level": "low",
    "expected_outcome": "Pod will restart with fresh state, clearing memory leak",
    "verification_command": "kubectl get pod -n production | grep api-server"
  }},
  {{
    "description": "Increase memory limit to prevent OOM",
    "command": "kubectl set resources deployment api-server -n production --limits=memory=1Gi",
    "risk_level": "low",
    "expected_outcome": "Pod will have more memory headroom",
    "verification_command": "kubectl get deployment api-server -n production -o jsonpath='{{.spec.template.spec.containers[0].resources.limits.memory}}'"
  }}
]

Provide ONLY the JSON array, no other text.
"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Parse JSON
            actions_data = self._parse_json_response(response_text)

            # Convert to Action objects
            actions = []
            for action_dict in actions_data:
                actions.append(Action(
                    description=action_dict.get("description", ""),
                    command=action_dict.get("command"),
                    risk_level=action_dict.get("risk_level", "medium"),
                    expected_outcome=action_dict.get("expected_outcome", ""),
                    verification_command=action_dict.get("verification_command")
                ))

            return actions

        except Exception as e:
            logger.error(f"Action generation failed: {e}", exc_info=True)
            return []
