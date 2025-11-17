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


def get_docker_status(compose_dir: Path, compose_cmd: List[str], compose_file: Path) -> Dict[str, str]:
    """
    Query Docker Compose for the current status of all services.
    
    Executes 'docker compose ps -a' (or 'docker-compose ps -a') with the compose
    file explicitly specified to get the current state of all services.
    
    Args:
        compose_dir: Directory containing the compose.yaml file
        compose_cmd: Docker Compose command to use (from detect_docker_compose_command)
        compose_file: Path to the compose file (used with -f flag)
    
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
    
    try:
        # Use absolute path for the compose file to ensure Docker Compose finds it reliably
        # This works regardless of the current working directory
        compose_file_abs = str(compose_file.resolve())
        
        if is_v2:
            # Docker Compose V2 supports --format flag
            cmd = compose_cmd + ["-f", compose_file_abs, "ps", "-a", "--format", "{{.Service}}\t{{.State}}\t{{.Name}}"]
        else:
            # Docker Compose V1 doesn't support --format, use default output
            cmd = compose_cmd + ["-f", compose_file_abs, "ps", "-a"]
        
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
        
        # Check if command failed
        if result.returncode != 0:
            # Log error for debugging, but don't fail completely
            # This can happen if services don't exist yet, or Docker daemon is down
            if result.stderr:
                # Only log to stderr if there's an actual error message
                # This helps with debugging without being too verbose
                pass  # Silently continue - will show "not created" for all services
        
        # Parse the output if command succeeded
        if result.returncode == 0 and result.stdout.strip():
            if is_v2:
                # V2 format: tab-separated Service, State, Name
                for line in result.stdout.strip().split("\n"):
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        service = parts[0]
                        state = parts[1]
                        status_map[service] = state
            else:
                # V1 format: table with columns NAME, IMAGE, COMMAND, SERVICE, CREATED, STATUS, PORTS
                # Parse the table output - columns are space-separated but variable width
                lines = result.stdout.strip().split("\n")
                if len(lines) < 2:
                    return status_map
                
                # Parse header to find column positions
                header = lines[0]
                # Find SERVICE and STATUS column positions
                service_idx = header.find("SERVICE")
                status_idx = header.find("STATUS")
                
                if service_idx == -1 or status_idx == -1:
                    # Fallback: try to parse without header positions
                    for line in lines[1:]:
                        if not line.strip():
                            continue
                        # Try to extract service name and status using common patterns
                        # Service name is usually a simple word, status starts with Up/Exited/etc
                        parts = line.split()
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
                                    break
                                elif part_lower.startswith("exited"):
                                    if i >= 1:
                                        service = parts[i-1] if i-1 < len(parts) else None
                                        state = "exited"
                                        if service:
                                            status_map[service] = state
                                    break
                                elif part_lower.startswith("created"):
                                    if i >= 1:
                                        service = parts[i-1] if i-1 < len(parts) else None
                                        state = "created"
                                        if service:
                                            status_map[service] = state
                                    break
                else:
                    # Parse using column positions
                    for line in lines[1:]:
                        if not line.strip() or len(line) < max(service_idx, status_idx):
                            continue
                        
                        # Extract service name from SERVICE column
                        # Find the end of SERVICE column (next column starts)
                        service_end = status_idx
                        service = line[service_idx:service_end].strip()
                        
                        # Extract status from STATUS column (until PORTS or end)
                        ports_idx = header.find("PORTS")
                        if ports_idx != -1 and len(line) > ports_idx:
                            status = line[status_idx:ports_idx].strip()
                        else:
                            status = line[status_idx:].strip()
                        
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
                        
                        if service:
                            status_map[service] = state
    except FileNotFoundError:
        # Docker command not found - user needs to install Docker
        print("Error: docker compose command not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Silently fail if docker compose fails
        # This can happen if services don't exist yet, or Docker daemon is down
        # We'll just show "not created" for all services in that case
        pass
    
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
    
    # Initialize Rich console for colored terminal output
    # Rich automatically detects terminal capabilities and adjusts output
    console = Console()
    
    # Detect which Docker Compose command is available
    try:
        compose_cmd = detect_docker_compose_command()
    except FileNotFoundError:
        console.print("[bold red]Error: Neither 'docker compose' nor 'docker-compose' command found![/bold red]")
        console.print("[yellow]Please install Docker Compose V2 or V1[/yellow]")
        sys.exit(1)
    
    # Step 1: Locate the Docker Compose file
    compose_file = get_compose_file(args.compose_file)
    
    # Validate that the compose file exists
    if not compose_file.exists():
        console.print(f"[bold red]Error: {compose_file} not found![/bold red]")
        sys.exit(1)
    
    # Step 2: Extract service names from the compose file
    services = extract_services(compose_file)
    
    # Handle empty compose files gracefully
    if not services:
        console.print(f"[bold yellow]No services found in {compose_file}[/bold yellow]")
        sys.exit(0)
    
    # Step 3: Query Docker for current service statuses
    # Must run from compose file directory so Docker finds the right file
    compose_dir = compose_file.parent
    status_map = get_docker_status(compose_dir, compose_cmd, compose_file)
    
    # Step 4: Display the status report
    
    # Print header with compose file location
    console.print(f"[bold bright_blue]Docker Compose Status[/bold bright_blue] [bright_cyan](from {compose_file})[/bright_cyan]")
    console.print("[bright_magenta]────────────────────────────────────────────[/bright_magenta]")
    
    # Display each service with its status
    for service in services:
        # Get the current state from Docker (None if not found)
        state = status_map.get(service)
        
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
