#!/usr/bin/env python3
"""
compose-status.py – Ultimate colorful Docker Compose service status
Cross-platform Python version

This script provides a beautiful, colorized overview of Docker Compose service statuses.
It reads a docker-compose.yaml file, extracts service names, queries Docker for their
current states, and displays them with intuitive color-coded icons and status indicators.

Author: Caerie Houchins (cdhouch)
License: MIT
GitHub: https://github.com/cdhouch/compose-status
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Import YAML parser for reading compose files
# PyYAML is a popular, safe YAML parser for Python
try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# Import Rich library for beautiful terminal output
# Rich provides cross-platform color support and advanced formatting
try:
    from rich.console import Console
    from rich.text import Text
except ImportError:
    print("Error: rich is required. Install with: pip install rich", file=sys.stderr)
    sys.exit(1)


def get_compose_file(compose_file_arg: Optional[str] = None) -> Path:
    """
    Get the Docker Compose file path.
    
    Priority order:
    1. Command-line argument (if provided)
    2. COMPOSE_FILE environment variable
    3. Default: ~/compose.yaml
    
    Args:
        compose_file_arg: Optional path to compose file from command-line argument
    
    Returns:
        Path: The path to the compose file (with ~ expanded to home directory)
    
    Example:
        >>> get_compose_file()
        Path('/home/user/compose.yaml')
        >>> get_compose_file('/path/to/compose.yaml')
        Path('/path/to/compose.yaml')
    """
    # Priority: command-line arg > environment variable > default
    if compose_file_arg:
        compose_file = compose_file_arg
    else:
        compose_file = os.environ.get("COMPOSE_FILE", str(Path.home() / "compose.yaml"))
    # Expand ~ to actual home directory path (cross-platform)
    return Path(compose_file).expanduser()


def detect_docker_compose_command() -> List[str]:
    """
    Detect which Docker Compose command is available on the system.
    
    Tries Docker Compose V2 (`docker compose`) first, then falls back to
    V1 (`docker-compose`) if V2 is not available.
    
    Returns:
        List[str]: Command to use for docker compose operations
        e.g., ['docker', 'compose'] or ['docker-compose']
    
    Raises:
        FileNotFoundError: If neither docker compose command is found
    """
    # Try Docker Compose V2 first (docker compose)
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return ["docker", "compose"]
    except FileNotFoundError:
        pass
    
    # Fall back to Docker Compose V1 (docker-compose)
    try:
        result = subprocess.run(
            ["docker-compose", "version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return ["docker-compose"]
    except FileNotFoundError:
        pass
    
    # Neither command found
    raise FileNotFoundError("Neither 'docker compose' nor 'docker-compose' command found")


def extract_services(compose_file: Path) -> List[str]:
    """
    Extract top-level service names from a Docker Compose YAML file.
    
    Parses the compose file and extracts all service names defined under the
    'services' key. Services are returned in alphabetical order for consistent
    display.
    
    Args:
        compose_file: Path to the docker-compose.yaml file
    
    Returns:
        List[str]: Sorted list of service names, or empty list if none found
    
    Example:
        >>> extract_services(Path("compose.yaml"))
        ['audiobookshelf', 'calibre-web', 'nginx-proxy-manager']
    """
    try:
        # Read and parse the YAML file
        # safe_load() prevents arbitrary code execution (security best practice)
        with open(compose_file, "r") as f:
            data = yaml.safe_load(f)
        
        # Validate that the file contains a services section
        if not data or "services" not in data:
            return []
        
        # Extract service names (keys of the services dictionary)
        # Sort for consistent, predictable output order
        services = list(data["services"].keys())
        return sorted(services)
    except yaml.YAMLError as e:
        # Handle YAML parsing errors gracefully
        # This could happen with malformed compose files
        print(f"Error parsing YAML: {e}", file=sys.stderr)
        return []


def debug_print(message: str, debug: bool = False):
    """
    Print debug message to stderr if debug mode is enabled.
    
    Args:
        message: Debug message to print
        debug: Whether debug mode is enabled
    """
    if debug:
        print(f"[DEBUG] {message}", file=sys.stderr)


def get_docker_status(compose_dir: Path, compose_cmd: List[str], compose_file: Path, debug: bool = False) -> Dict[str, str]:
    """
    Query Docker Compose for the current status of all services.
    
    Executes 'docker compose ps -a' (or 'docker-compose ps -a') with the compose
    file explicitly specified to get the current state of all services.
    
    Args:
        compose_dir: Directory containing the compose.yaml file
        compose_cmd: Docker Compose command to use (from detect_docker_compose_command)
        compose_file: Path to the compose file (used with -f flag)
        debug: Whether to enable debug logging
    
    Returns:
        Dict[str, str]: Dictionary mapping service names to their states
                       (e.g., {'nginx': 'running', 'db': 'stopped'})
    
    Note:
        Common Docker Compose states include:
        - 'running': Container is currently running
        - 'exited': Container stopped normally
        - 'dead': Container failed to start or crashed
        - 'created': Container created but not started
        - 'stopped': Container was explicitly stopped
    """
    status_map = {}
    is_v2 = compose_cmd == ["docker", "compose"]
    
    debug_print(f"Getting Docker status - compose_dir: {compose_dir}, compose_file: {compose_file}", debug)
    debug_print(f"Docker Compose command: {compose_cmd}, is_v2: {is_v2}", debug)
    
    try:
        # Use absolute path for the compose file to ensure Docker Compose finds it reliably
        # This works regardless of the current working directory
        compose_file_abs = str(compose_file.resolve())
        debug_print(f"Resolved compose file path: {compose_file_abs}", debug)
        
        if is_v2:
            # Docker Compose V2 supports --format flag
            cmd = compose_cmd + ["-f", compose_file_abs, "ps", "-a", "--format", "{{.Service}}\t{{.State}}\t{{.Name}}"]
        else:
            # Docker Compose V1 doesn't support --format, use default output
            cmd = compose_cmd + ["-f", compose_file_abs, "ps", "-a"]
        
        debug_print(f"Executing command: {' '.join(cmd)}", debug)
        debug_print(f"Working directory: {compose_dir}", debug)
        
        # Run docker compose ps from the compose file directory
        # -a flag includes stopped containers
        # -f flag explicitly specifies the compose file
        result = subprocess.run(
            cmd,
            cwd=compose_dir,
            capture_output=True,  # Capture both stdout and stderr
            text=True,            # Return string output instead of bytes
            check=False,          # Don't raise exception on non-zero exit
        )
        
        debug_print(f"Command return code: {result.returncode}", debug)
        debug_print(f"Command stdout length: {len(result.stdout)} characters", debug)
        debug_print(f"Command stderr length: {len(result.stderr)} characters", debug)
        
        if result.stdout:
            debug_print(f"Command stdout:\n{result.stdout}", debug)
        if result.stderr:
            debug_print(f"Command stderr:\n{result.stderr}", debug)
        
        # Check if command failed
        if result.returncode != 0:
            debug_print(f"Command failed with return code {result.returncode}", debug)
            # Log error for debugging, but don't fail completely
            # This can happen if services don't exist yet, or Docker daemon is down
            if result.stderr:
                # Only log to stderr if there's an actual error message
                # This helps with debugging without being too verbose
                pass  # Silently continue - will show "not created" for all services
        
        # Parse the output if command succeeded
        if result.returncode == 0 and result.stdout.strip():
            debug_print("Parsing command output...", debug)
            if is_v2:
                # V2 format: tab-separated Service, State, Name
                debug_print("Using V2 format parser", debug)
                for line in result.stdout.strip().split("\n"):
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        service = parts[0]
                        state = parts[1]
                        status_map[service] = state
                        debug_print(f"  Parsed: service={service}, state={state}", debug)
            else:
                # V1 format: table with columns NAME, IMAGE, COMMAND, SERVICE, CREATED, STATUS, PORTS
                # Parse the table output - columns are space-separated but variable width
                debug_print("Using V1 format parser", debug)
                lines = result.stdout.strip().split("\n")
                debug_print(f"Total lines in output: {len(lines)}", debug)
                if len(lines) < 2:
                    debug_print("Not enough lines in output (need at least header + 1 data line)", debug)
                    return status_map
                
                # Parse header to find column positions
                header = lines[0]
                debug_print(f"Header line: {header}", debug)
                # Find SERVICE, CREATED, and STATUS column positions
                service_idx = header.find("SERVICE")
                created_idx = header.find("CREATED")
                status_idx = header.find("STATUS")
                debug_print(f"Column positions - SERVICE: {service_idx}, CREATED: {created_idx}, STATUS: {status_idx}", debug)
                
                if service_idx == -1 or status_idx == -1:
                    # Fallback: try to parse without header positions
                    debug_print("SERVICE or STATUS column not found in header, using fallback parser", debug)
                    for line in lines[1:]:
                        if not line.strip():
                            continue
                        debug_print(f"  Parsing line: {line}", debug)
                        # Try to extract service name and status using common patterns
                        # Service name is usually a simple word, status starts with Up/Exited/etc
                        parts = line.split()
                        debug_print(f"  Line parts: {parts}", debug)
                        if len(parts) >= 4:
                            # Look for status indicators
                            for i, part in enumerate(parts):
                                part_lower = part.lower()
                                if part_lower.startswith("up"):
                                    # Found status, service is likely a few columns before
                                    if i >= 1:
                                        service = parts[i-1] if i-1 < len(parts) else None
                                        state = "running"
                                        if service:
                                            status_map[service] = state
                                            debug_print(f"  Fallback parsed: service={service}, state={state}", debug)
                                    break
                                elif part_lower.startswith("exited"):
                                    if i >= 1:
                                        service = parts[i-1] if i-1 < len(parts) else None
                                        state = "exited"
                                        if service:
                                            status_map[service] = state
                                            debug_print(f"  Fallback parsed: service={service}, state={state}", debug)
                                    break
                                elif part_lower.startswith("created"):
                                    if i >= 1:
                                        service = parts[i-1] if i-1 < len(parts) else None
                                        state = "created"
                                        if service:
                                            status_map[service] = state
                                            debug_print(f"  Fallback parsed: service={service}, state={state}", debug)
                                    break
                else:
                    # Parse using column positions
                    debug_print(f"Using column-based parser for {len(lines)-1} data lines", debug)
                    for line in lines[1:]:
                        if not line.strip() or len(line) < max(service_idx, status_idx):
                            debug_print(f"  Skipping line (too short or empty): {line[:50]}...", debug)
                            continue
                        
                        debug_print(f"  Parsing line: {line}", debug)
                        
                        # Extract service name from SERVICE column
                        # Find the end of SERVICE column (CREATED column starts next)
                        # If CREATED column not found, fall back to STATUS column
                        if created_idx != -1 and created_idx > service_idx:
                            service_end = created_idx
                        else:
                            service_end = status_idx
                        service = line[service_idx:service_end].strip()
                        
                        # Extract status from STATUS column (until PORTS or end)
                        ports_idx = header.find("PORTS")
                        if ports_idx != -1 and len(line) > ports_idx:
                            status = line[status_idx:ports_idx].strip()
                        else:
                            status = line[status_idx:].strip()
                        
                        debug_print(f"  Extracted: service='{service}', status='{status}'", debug)
                        
                        # Normalize status
                        status_lower = status.lower()
                        if status_lower.startswith("up"):
                            state = "running"
                        elif status_lower.startswith("exited"):
                            state = "exited"
                        elif status_lower.startswith("created"):
                            state = "created"
                        elif status_lower.startswith("dead"):
                            state = "dead"
                        elif status_lower.startswith("stopped"):
                            state = "stopped"
                        else:
                            state = status_lower.split()[0] if status_lower.split() else "unknown"
                        
                        debug_print(f"  Normalized state: '{state}'", debug)
                        
                        if service:
                            status_map[service] = state
                            debug_print(f"  Parsed: service={service}, state={state}", debug)
                        else:
                            debug_print(f"  Skipping: service name is empty", debug)
    except FileNotFoundError:
        # Docker command not found - user needs to install Docker
        debug_print("Docker command not found", debug)
        print("Error: docker compose command not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Silently fail if docker compose fails
        # This can happen if services don't exist yet, or Docker daemon is down
        # We'll just show "not created" for all services in that case
        debug_print(f"Exception occurred: {type(e).__name__}: {e}", debug)
        import traceback
        debug_print(f"Traceback:\n{traceback.format_exc()}", debug)
    
    debug_print(f"Final status_map: {status_map}", debug)
    return status_map


def get_status_display(state: Optional[str]) -> tuple[str, str]:
    """
    Map a Docker service state to a visual icon and display text.
    
    Converts Docker Compose service states into user-friendly visual indicators.
    Uses emoji icons and descriptive text that will be colorized in the output.
    
    Args:
        state: The Docker service state (e.g., 'running', 'exited', None)
    
    Returns:
        tuple[str, str]: A tuple of (icon_emoji, status_text)
    
    State Mappings:
        - None: ⚪ "not created" (service not found in Docker)
        - "running": 🟢 "running" (service is active)
        - "exited"/"dead"/"stopped": 🔴 "stopped" (service is not running)
        - "created": 🟦 "created" (container exists but not started)
        - Other: 🟡 <state> (unknown state, show as-is)
    """
    if state is None:
        # Service not found in Docker - container was never created
        return "⚪", "not created"
    
    # Normalize state to lowercase for case-insensitive comparison
    state_lower = state.lower()
    
    if state_lower == "running":
        # Service is healthy and running
        return "🟢", "running"
    elif state_lower in ("exited", "dead", "stopped"):
        # Service is not running (various stopped states)
        return "🔴", "stopped"
    elif state_lower == "created":
        # Container created but not started
        return "🟦", "created"
    else:
        # Unknown or uncommon state - display as-is
        return "🟡", state


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="A beautiful, colorized command-line tool for quickly viewing the status of all services in your Docker Compose setup.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --file /path/to/compose.yaml
  %(prog)s -f ./docker-compose.yml
  %(prog)s --debug -f docker-compose.yaml

The script will check for compose files in this order:
  1. Command-line --file argument
  2. COMPOSE_FILE environment variable
  3. Default: ~/compose.yaml
        """
    )
    parser.add_argument(
        "-f", "--file",
        dest="compose_file",
        metavar="FILE",
        help="Path to Docker Compose file (default: ~/compose.yaml or COMPOSE_FILE env var)"
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug logging to diagnose issues"
    )
    return parser.parse_args()


def main():
    """
    Main entry point for the compose-status script.
    
    Orchestrates the entire workflow:
    1. Parses command-line arguments
    2. Detects available Docker Compose command
    3. Locates the compose file
    4. Extracts service names
    5. Queries Docker for service statuses
    6. Displays a beautiful, colorized status report
    """
    # Parse command-line arguments
    args = parse_arguments()
    debug = args.debug
    
    if debug:
        debug_print("Debug mode enabled", debug)
    
    # Initialize Rich console for colored terminal output
    # Rich automatically detects terminal capabilities and adjusts output
    console = Console()
    
    # Detect which Docker Compose command is available
    try:
        compose_cmd = detect_docker_compose_command()
        debug_print(f"Detected Docker Compose command: {compose_cmd}", debug)
    except FileNotFoundError:
        console.print("[bold red]Error: Neither 'docker compose' nor 'docker-compose' command found![/bold red]")
        console.print("[yellow]Please install Docker Compose V2 or V1[/yellow]")
        sys.exit(1)
    
    # Step 1: Locate the Docker Compose file
    compose_file = get_compose_file(args.compose_file)
    debug_print(f"Using compose file: {compose_file}", debug)
    debug_print(f"Compose file exists: {compose_file.exists()}", debug)
    
    # Validate that the compose file exists
    if not compose_file.exists():
        console.print(f"[bold red]Error: {compose_file} not found![/bold red]")
        sys.exit(1)
    
    # Step 2: Extract service names from the compose file
    services = extract_services(compose_file)
    debug_print(f"Extracted services from compose file: {services}", debug)
    
    # Handle empty compose files gracefully
    if not services:
        console.print(f"[bold yellow]No services found in {compose_file}[/bold yellow]")
        sys.exit(0)
    
    # Step 3: Query Docker for current service statuses
    # Must run from compose file directory so Docker finds the right file
    compose_dir = compose_file.parent
    debug_print(f"Compose directory: {compose_dir}", debug)
    status_map = get_docker_status(compose_dir, compose_cmd, compose_file, debug)
    debug_print(f"Retrieved status map with {len(status_map)} entries", debug)
    
    # Step 4: Display the status report
    
    # Print header with compose file location
    console.print(f"[bold bright_blue]Docker Compose Status[/bold bright_blue] [bright_cyan](from {compose_file})[/bright_cyan]")
    console.print("[bright_magenta]────────────────────────────────────────────[/bright_magenta]")
    
    # Display each service with its status
    for service in services:
        # Get the current state from Docker (None if not found)
        state = status_map.get(service)
        debug_print(f"Service '{service}': state={state} (from status_map)", debug)
        
        # Get appropriate icon and text for this state
        icon, status_text = get_status_display(state)
        
        # Build formatted service name (left-aligned, 22 chars wide)
        service_text = Text(f"  {service:<22}", style="bold bright_cyan")
        
        # Apply color coding based on service state
        # Colors match the icon meanings for visual consistency
        if state is None:
            # Yellow for "not created" - neutral/warning state
            icon_text = Text(icon, style="yellow")
            status_display = Text(status_text, style="yellow")
        elif state.lower() == "running":
            # Green for running - healthy state
            icon_text = Text(icon, style="bright_green")
            status_display = Text(status_text, style="bright_green")
        elif state.lower() in ("exited", "dead", "stopped"):
            # Red for stopped - needs attention
            icon_text = Text(icon, style="bright_red")
            status_display = Text(status_text, style="bright_red")
        elif state.lower() == "created":
            # Cyan for created - intermediate state
            icon_text = Text(icon, style="bright_cyan")
            status_display = Text(status_text, style="bright_cyan")
        else:
            # Yellow for unknown states - caution
            icon_text = Text(icon, style="yellow")
            status_display = Text(status_text, style="yellow")
        
        # Combine all parts and print the formatted line
        output = service_text + " " + icon_text + " " + status_display
        console.print(output)
    
    # Print footer with helpful tip
    console.print("[bright_magenta]────────────────────────────────────────────[/bright_magenta]")
    home = Path.home()
    console.print(f"[bold bright_cyan]Tip:[/bold bright_cyan] Run 'cd {home} && docker compose ps -a' for full details.")


if __name__ == "__main__":
    main()
