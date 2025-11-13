"""
Sherlock SRE - Main Application Entry Point

Starts the Slack bot and runs the investigation service.
"""

import asyncio
import logging
import sys
from typing import Optional

from .config import settings
from .investigator import Investigator
from .interfaces import SherlockSlackBot


# Configure logging
def setup_logging():
    """Configure logging with appropriate level and format"""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("kubernetes").setLevel(logging.WARNING)
    logging.getLogger("slack_sdk").setLevel(logging.INFO)


logger = logging.getLogger(__name__)


class SherlockApp:
    """
    Main Sherlock application

    Manages the lifecycle of all components
    """

    def __init__(self):
        """Initialize the application"""
        self.investigator: Optional[Investigator] = None
        self.slack_bot: Optional[SherlockSlackBot] = None

    async def start(self):
        """
        Start the application

        Initializes all components and starts the Slack bot
        """
        logger.info("=" * 70)
        logger.info("Starting Sherlock SRE")
        logger.info("=" * 70)
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Log level: {settings.log_level}")
        logger.info(f"Auto-remediation: {'ENABLED' if settings.enable_auto_remediation else 'DISABLED'}")
        logger.info("=" * 70)

        try:
            # Initialize investigator
            logger.info("Initializing investigator...")
            self.investigator = Investigator()

            # Run diagnostics
            logger.info("Running diagnostics...")
            diagnostics = await self.investigator.run_diagnostics()

            logger.info("Component Health:")
            for component, status in diagnostics["components"].items():
                status_emoji = "✅" if status["healthy"] else "❌"
                logger.info(f"  {status_emoji} {component}: {status['status']}")

            if diagnostics["overall_status"] != "healthy":
                logger.warning("⚠️  Some components are unhealthy, but continuing...")

            # Initialize and start Slack bot
            logger.info("Initializing Slack bot...")
            self.slack_bot = SherlockSlackBot(self.investigator)

            logger.info("✅ Sherlock is ready!")
            logger.info("=" * 70)
            logger.info("Starting Slack bot... (Ctrl+C to stop)")

            # Start the bot (this blocks)
            await self.slack_bot.start()

        except KeyboardInterrupt:
            logger.info("\n🛑 Shutting down gracefully...")
            await self.shutdown()

        except Exception as e:
            logger.error(f"❌ Fatal error: {e}", exc_info=True)
            await self.shutdown()
            sys.exit(1)

    async def shutdown(self):
        """
        Graceful shutdown

        Cleans up resources
        """
        logger.info("Shutting down Sherlock...")

        # TODO: Close database connections, save state, etc.

        logger.info("Shutdown complete")


async def main():
    """Main entry point"""
    setup_logging()

    app = SherlockApp()
    await app.start()


def run():
    """Run the application"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    run()
