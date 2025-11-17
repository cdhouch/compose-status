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


def get_compose_file() -> Path:
    """
    Get the Docker Compose file path.
    
    Checks the COMPOSE_FILE environment variable first, then defaults to
    ~/compose.yaml. This allows users to specify a custom compose file location.
    
    Returns:
        Path: The path to the compose file (with ~ expanded to home directory)
    
    Example:
        >>> get_compose_file()
        Path('/home/user/compose.yaml')
    """
    # Check for custom compose file location via environment variable
    # This allows flexibility for different project structures
    compose_file = os.environ.get("COMPOSE_FILE", str(Path.home() / "compose.yaml"))
    # Expand ~ to actual home directory path (cross-platform)
    return Path(compose_file).expanduser()


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


def get_docker_status(compose_dir: Path) -> Dict[str, str]:
    """
    Query Docker Compose for the current status of all services.
    
    Executes 'docker compose ps -a' from the compose file's directory to get
    the current state of all services. The command must be run from the compose
    file directory so Docker can find the correct compose.yaml file.
    
    Args:
        compose_dir: Directory containing the compose.yaml file
    
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
    
    try:
        # Run docker compose ps from the compose file directory
        # -a flag includes stopped containers
        # --format uses Go template syntax for tab-separated output
        # We change to the compose directory so Docker finds the right compose file
        result = subprocess.run(
            ["docker", "compose", "ps", "-a", "--format", "{{.Service}}\t{{.State}}\t{{.Name}}"],
            cwd=compose_dir,
            capture_output=True,  # Capture both stdout and stderr
            text=True,            # Return string output instead of bytes
            check=False,          # Don't raise exception on non-zero exit
        )
        
        # Parse the output if command succeeded
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                # Split tab-separated values: Service, State, Name
                parts = line.split("\t")
                if len(parts) >= 2:
                    service = parts[0]
                    state = parts[1]
                    # Store service name -> state mapping
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


def main():
    """
    Main entry point for the compose-status script.
    
    Orchestrates the entire workflow:
    1. Locates the compose file
    2. Extracts service names
    3. Queries Docker for service statuses
    4. Displays a beautiful, colorized status report
    """
    # Initialize Rich console for colored terminal output
    # Rich automatically detects terminal capabilities and adjusts output
    console = Console()
    
    # Step 1: Locate the Docker Compose file
    compose_file = get_compose_file()
    
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
    status_map = get_docker_status(compose_dir)
    
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

