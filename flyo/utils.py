"""
Utility functions for CLI colors, logging, and helpers.
"""

import sys
from typing import List, Dict, Any


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    @staticmethod
    def success(msg: str) -> str:
        return f"{Colors.GREEN}✓ {msg}{Colors.END}"
    
    @staticmethod
    def warning(msg: str) -> str:
        return f"{Colors.YELLOW}⚠ {msg}{Colors.END}"
    
    @staticmethod
    def error(msg: str) -> str:
        return f"{Colors.RED}✗ {msg}{Colors.END}"
    
    @staticmethod
    def info(msg: str) -> str:
        return f"{Colors.CYAN}ℹ {msg}{Colors.END}"
    
    @staticmethod
    def progress(msg: str) -> str:
        return f"{Colors.BLUE}→ {msg}{Colors.END}"
    
    @staticmethod
    def bold(msg: str) -> str:
        return f"{Colors.BOLD}{msg}{Colors.END}"


def print_banner():
    """Print FLYO welcome banner"""
    banner = f"""{Colors.BOLD}{Colors.CYAN}
╔══════════════════════════════════════════════════════════╗
║           FLYO - Natural Language Browser Bot            ║
║         Turn Words Into Web Actions (24-hr Build)        ║
╚══════════════════════════════════════════════════════════╝
{Colors.END}"""
    print(banner)


def format_action_plan(plan: List[Dict[str, Any]]) -> str:
    """Format action plan for display"""
    lines = [f"\n{Colors.bold('Generated Action Plan:')}"]
    
    for i, action in enumerate(plan, 1):
        action_type = action.get("action", "unknown").upper()
        line = f"  {i}. {Colors.BLUE}{action_type}{Colors.END}"
        
        if action_type == "NAVIGATE":
            line += f" → {action.get('url', '')}"
        elif action_type == "CLICK":
            line += f" on {action.get('selector', '')}"
        elif action_type == "TYPE":
            text = action.get('text', '')
            if len(text) > 30:
                text = text[:30] + "..."
            line += f" → '{text}' into {action.get('selector', '')}"
        elif action_type == "WAIT":
            line += f" for {action.get('selector', '')} ({action.get('timeout', 10)}s)"
        elif action_type == "SCROLL":
            line += f" {action.get('direction', 'down')} by {action.get('amount', 3)}"
        elif action_type == "EXTRACT":
            line += f" {action.get('property', 'text')} from {action.get('selector', '')}"
        elif action_type == "SUBMIT_FORM":
            line += f" at {action.get('selector', '')}"
        
        lines.append(line)
    
    return "\n".join(lines)


def prompt_approval(plan: List[Dict]) -> bool:
    """Interactive approval prompt"""
    print(format_action_plan(plan))
    
    # Check for risky actions
    risky = {"submit_form", "submit_payment", "delete"}
    has_risky = any(a.get("action") in risky for a in plan)
    
    if has_risky:
        print(f"\n{Colors.warning('This plan includes high-risk actions (form submission, etc.)')}")
    
    response = input(f"\n{Colors.bold('Execute this plan? (y/n): ')}").strip().lower()
    return response in ('y', 'yes')


def format_execution_summary(result: Dict[str, Any]) -> str:
    """Format execution result for display"""
    lines = [
        f"\n{Colors.bold('╔════════════════════════════════════════╗')}",
        f"{Colors.bold('║           EXECUTION RESULT              ║')}",
        f"{Colors.bold('╚════════════════════════════════════════╝')}\n"
    ]
    
    status = result.get("status", "unknown")
    if status == "success":
        lines.append(Colors.success(f"Status: {status}"))
    else:
        lines.append(Colors.error(f"Status: {status}"))
    
    lines.append(f"  Request: {result.get('request', 'N/A')}")
    lines.append(f"  Steps planned: {result.get('steps_planned', 0)}")
    lines.append(f"  Steps executed: {result.get('steps_executed', 0)}")
    lines.append(f"  Success rate: {result.get('success_rate', 'N/A')}")
    lines.append(f"  Elapsed time: {result.get('elapsed_time', 'N/A')}")
    lines.append(f"  Final state: {result.get('state', 'N/A')}")
    
    if result.get('self_heal_attempts', 0) > 0:
        lines.append(f"  Self-heal attempts: {result.get('self_heal_attempts')}")
    
    if result.get('error'):
        error_text = f"Error: {result['error']}"
        lines.append(f"\n{Colors.error(error_text)}")

    return "\n".join(lines)


def load_site_config(config_path: str) -> Dict[str, Any]:
    """Load site-specific configuration from JSON file"""
    import json
    from pathlib import Path
    
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r') as f:
        return json.load(f)


def save_execution_log(result: Dict[str, Any], log_path: str) -> None:
    """Save execution result to log file"""
    import json
    from pathlib import Path
    from datetime import datetime
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        **result
    }
    
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to log file
    with open(path, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")
