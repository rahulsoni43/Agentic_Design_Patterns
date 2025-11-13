"""
Interfaces for Sherlock SRE

User-facing interfaces (Slack bot, API, CLI)
"""

from .slack_bot import SherlockSlackBot

__all__ = ["SherlockSlackBot"]
