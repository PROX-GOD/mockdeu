import asyncio
import logging
import sys
from termcolor import colored

from mockdeu.config import Config
from mockdeu.logic.session import InterviewSession
from mockdeu.interfaces.cli import CLIInterface
from mockdeu.interfaces.gui import GUIInterface

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose third-party logs
logging.getLogger("a4f_local").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("comtypes").setLevel(logging.ERROR)

async def main():
    """Main entry point"""
    try:
        cfg = Config()
    except ValueError as e:
        logger.error(str(e))
        print(colored(f"Configuration Error: {e}", "red"))
        return

    print(colored("\n=== MockDeu Visa Simulator ===\n", "cyan", attrs=["bold"]))
    print("Select Interface Mode:")
    print("1. CLI (Terminal)")
    print("2. GUI (Graphical Window)")
    
    mode = input("Choice (1/2): ").strip()
    
    if mode == "2":
        interface = GUIInterface()
    else:
        interface = CLIInterface()
        
    session = InterviewSession(cfg, interface)
    await session.run()

def run():
    """Synchronous wrapper for async main"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    run()
