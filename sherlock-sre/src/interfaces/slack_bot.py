"""
Slack Bot Interface for Sherlock SRE

Provides conversational interface for incident investigation.
Uses Slack Bolt framework for modern async support.
"""

import asyncio
import logging
from typing import Optional

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from ..config import settings
from ..investigator import Investigator
from ..models import Investigation

logger = logging.getLogger(__name__)


class SherlockSlackBot:
    """
    Slack bot for conversational incident investigation

    Commands:
    - @sherlock investigate <issue> - Start investigation
    - @sherlock help - Show help message
    - @sherlock status - Show bot status
    """

    def __init__(self, investigator: Investigator):
        """
        Initialize Slack bot

        Args:
            investigator: The investigation orchestrator
        """
        self.investigator = investigator

        # Initialize Slack app
        self.app = AsyncApp(
            token=settings.slack_bot_token,
            signing_secret=settings.slack_signing_secret
        )

        # Register event handlers
        self._register_handlers()

        logger.info("Sherlock Slack bot initialized")

    def _register_handlers(self):
        """Register Slack event handlers"""

        # Handle app mentions (@sherlock ...)
        @self.app.event("app_mention")
        async def handle_mention(event, say):
            await self._handle_investigation_request(event, say)

        # Handle direct messages
        @self.app.event("message")
        async def handle_message(event, say):
            # Only respond to DMs (no channel_type means DM)
            if event.get("channel_type") == "im":
                await self._handle_investigation_request(event, say)

        # Handle slash commands
        @self.app.command("/sherlock")
        async def handle_command(ack, command, say):
            await ack()
            await self._handle_investigation_request(command, say)

    async def _handle_investigation_request(self, event, say):
        """
        Handle investigation request from user

        Args:
            event: Slack event data
            say: Function to send message back to Slack
        """
        try:
            # Extract query from message
            text = event.get("text", "")
            user_id = event.get("user", "unknown")

            # Remove bot mention if present
            text = text.replace(f"<@{event.get('bot_id', '')}>", "").strip()

            # Handle special commands
            if not text or "help" in text.lower():
                await say(self._format_help_message())
                return

            if "status" in text.lower():
                await say(self._format_status_message())
                return

            # Send "thinking" message
            thinking_msg = await say(
                f"🔍 Investigating: _{text}_\n\n_Gathering data from your cluster..._"
            )

            # Run investigation
            investigation = await self.investigator.investigate(
                query=text,
                user_id=user_id
            )

            # Format and send response
            response_blocks = self._format_investigation_response(investigation)

            await say(
                blocks=response_blocks,
                text=f"Investigation complete: {investigation.analysis.root_cause if investigation.analysis else 'No root cause found'}"
            )

        except Exception as e:
            logger.error(f"Error handling investigation: {e}", exc_info=True)
            await say(
                f"❌ Sorry, something went wrong: {str(e)}\n\n"
                f"Please try again or contact your SRE team."
            )

    def _format_investigation_response(self, investigation: Investigation) -> list:
        """
        Format investigation results as Slack blocks

        Uses Slack Block Kit for rich formatting
        """
        blocks = []

        # Header
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "info": "🔵"
        }

        # Determine overall severity from events
        severities = [e.severity.value for e in investigation.events]
        max_severity = "info"
        if "critical" in severities:
            max_severity = "critical"
        elif "high" in severities:
            max_severity = "high"
        elif "medium" in severities:
            max_severity = "medium"

        emoji = severity_emoji.get(max_severity, "⚪")

        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} Investigation Complete"
            }
        })

        blocks.append({"type": "divider"})

        # Root cause section
        if investigation.analysis:
            confidence_bar = "█" * int(investigation.analysis.confidence * 10) + "░" * (10 - int(investigation.analysis.confidence * 10))

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🎯 Root Cause*\n{investigation.analysis.root_cause}\n\n"
                           f"*Confidence:* {investigation.analysis.confidence:.0%} `{confidence_bar}`"
                }
            })

            # Evidence
            if investigation.analysis.evidence:
                evidence_text = "\n".join(f"• {e}" for e in investigation.analysis.evidence[:5])
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📋 Evidence*\n{evidence_text}"
                    }
                })

        # Events summary
        if investigation.events:
            events_by_type = {}
            for event in investigation.events:
                events_by_type[event.event_type.value] = events_by_type.get(event.event_type.value, 0) + 1

            events_summary = "\n".join(
                f"• {count}x {event_type.replace('_', ' ').title()}"
                for event_type, count in sorted(events_by_type.items(), key=lambda x: -x[1])[:5]
            )

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*⚠️ Issues Detected ({len(investigation.events)} total)*\n{events_summary}"
                }
            })

        blocks.append({"type": "divider"})

        # Recommended actions
        if investigation.recommended_actions:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🔧 Recommended Actions*"
                }
            })

            for i, action in enumerate(investigation.recommended_actions[:3], 1):
                risk_emoji = {"low": "✅", "medium": "⚠️", "high": "🚨"}.get(action.risk_level, "⚪")

                action_text = f"*{i}. {action.description}*\n"
                if action.command:
                    action_text += f"```{action.command}```\n"
                action_text += f"{risk_emoji} Risk: {action.risk_level} | Expected: {action.expected_outcome}"

                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": action_text
                    }
                })

        # Alternative causes (if any)
        if investigation.analysis and investigation.analysis.alternative_causes:
            alt_text = "\n".join(f"• {cause}" for cause in investigation.analysis.alternative_causes[:3])
            blocks.append({
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f"*Other Possible Causes:*\n{alt_text}"
                }]
            })

        # Footer
        blocks.append({
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f"Investigation ID: {investigation.id} | "
                       f"Analyzed {len(investigation.events)} events in {len(investigation.correlations)} correlations | "
                       f"Powered by Sherlock SRE"
            }]
        })

        return blocks

    def _format_help_message(self) -> str:
        """Format help message"""
        return """*🔍 Sherlock - AI-Powered SRE Investigation Copilot*

*How to Use:*
• `@sherlock investigate <issue>` - Start an investigation
• `@sherlock help` - Show this help
• `@sherlock status` - Check bot status

*Examples:*
• `@sherlock investigate API is returning 502s`
• `@sherlock investigate Why is my-app pod crashlooping?`
• `@sherlock investigate High memory usage in production`

*What I Do:*
✓ Collect data from Kubernetes, logs, and metrics
✓ Correlate events to find relationships
✓ Use AI to determine root causes
✓ Provide specific remediation steps with commands
✓ Learn from past incidents to get better over time

*Need Help?* Contact your SRE team or check the docs.
"""

    def _format_status_message(self) -> str:
        """Format status message"""
        # TODO: Add actual health checks
        return """*🤖 Sherlock Status*

✅ Slack bot: Online
✅ Kubernetes collector: Ready
✅ AI analyzer: Ready
✅ Database: Connected

*Configuration:*
• Environment: {env}
• Auto-remediation: {auto_fix}
• Incident learning: {learning}

All systems operational! 🚀
""".format(
            env=settings.environment,
            auto_fix="Enabled" if settings.enable_auto_remediation else "Disabled (safe mode)",
            learning="Enabled" if settings.enable_incident_learning else "Disabled"
        )

    async def start(self):
        """
        Start the Slack bot

        Uses Socket Mode for easier deployment (no webhook setup needed)
        """
        if not settings.slack_bot_token or not settings.slack_app_token:
            logger.error("Slack tokens not configured. Bot cannot start.")
            raise ValueError("Slack tokens not configured in settings")

        logger.info("Starting Sherlock Slack bot...")

        handler = AsyncSocketModeHandler(self.app, settings.slack_app_token)
        await handler.start_async()

    async def send_proactive_alert(
        self,
        channel: str,
        message: str,
        investigation: Optional[Investigation] = None
    ):
        """
        Send a proactive alert to a channel

        Used for predictive alerts (Phase 3 feature)

        Args:
            channel: Slack channel (e.g., #incidents)
            message: Alert message
            investigation: Optional investigation results
        """
        try:
            if investigation:
                blocks = self._format_investigation_response(investigation)
                blocks.insert(0, {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🔮 *Proactive Alert*\n{message}"
                    }
                })
            else:
                blocks = [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🔮 *Proactive Alert*\n{message}"
                    }
                }]

            await self.app.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=message
            )

            logger.info(f"Sent proactive alert to {channel}")

        except Exception as e:
            logger.error(f"Failed to send proactive alert: {e}")
