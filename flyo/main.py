"""
CLI entry point for FLYO.
Usage: python -m flyo "Your task here"
"""

import sys
import asyncio
import argparse
import logging
from pathlib import Path

from flyo import FlyoAgent, OpenAIPlanner, OllamaPlanner
from flyo.utils import (
    Colors, print_banner, prompt_approval, 
    format_execution_summary, load_site_config
)


def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="FLYO - Natural Language Browser Automation",
        epilog="Examples:\n"
               "  python -m flyo \"Search Google for automation\"\n"
               "  python -m flyo \"Book flight\" --config configs/flights.json\n"
               "  python -m flyo \"Your task\" --no-approval --headless",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "request",
        nargs="?",
        help="Your task in plain English"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to site-specific config JSON file"
    )
    
    parser.add_argument(
        "--no-approval",
        action="store_true",
        help="Skip approval step (auto-approve risky actions)"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (no window)"
    )
    
    parser.add_argument(
        "--model",
        default="gpt-3.5-turbo",
        help="LLM model (default: gpt-3.5-turbo, or use ollama/qwen:7b for local)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Action timeout in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="FLYO 1.0.0"
    )
    
    return parser.parse_args()


async def main_async():
    """Async main function"""
    args = parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Print banner
    print_banner()
    
    # Get user request
    if not args.request:
        args.request = input(f"{Colors.bold('What would you like me to do?')}\n> ").strip()
        if not args.request:
            print(Colors.error("No request provided"))
            sys.exit(1)
    
    print(Colors.info(f"Request: {args.request}"))
    print(Colors.info(f"Model: {args.model}"))
    
    # Load site config if provided
    site_instructions = ""
    if args.config:
        try:
            config = load_site_config(args.config)
            site_instructions = f"""
Site: {config.get('site_name', 'Unknown')}
Base URL: {config.get('base_url', '')}
Selectors: {config.get('selectors', {})}
Instructions: {config.get('instructions', '')}
"""
            print(Colors.info(f"Loaded config: {config.get('site_name', 'Unknown')}"))
        except Exception as e:
            print(Colors.warning(f"Could not load config: {e}"))
    
    # Initialize planner
    if args.model.startswith("ollama/"):
        model_name = args.model.replace("ollama/", "")
        planner = OllamaPlanner(model=model_name, site_instructions=site_instructions)
    else:
        planner = OpenAIPlanner(model=args.model, site_instructions=site_instructions)
    
    # Initialize agent
    agent = FlyoAgent(
        planner=planner,
        require_approval=not args.no_approval,
        headless=args.headless,
        timeout=args.timeout * 1000  # Convert to ms
    )
    
    # Set approval callback if interactive
    if not args.no_approval:
        agent.set_approval_callback(prompt_approval)
    
    # Set log callback for progress updates
    def log_callback(msg: str):
        print(Colors.progress(msg))
    
    agent.set_log_callback(log_callback)
    
    # Execute
    try:
        result = await agent.execute(args.request)
        
        # Print results
        print(format_execution_summary(result))
        
        # Exit with appropriate code
        sys.exit(0 if result["status"] == "success" else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.warning('Interrupted by user')}")
        sys.exit(130)
    
    except Exception as e:
        print(Colors.error(f"Fatal error: {e}"))
        sys.exit(1)


def main():
    """Entry point"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print(f"\n{Colors.warning('Interrupted')}")
        sys.exit(130)


if __name__ == "__main__":
    main()
