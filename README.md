# compose-status

A beautiful, colorized command-line tool for quickly viewing the status of all services in your Docker Compose setup at a glance.

![Status Example](https://img.shields.io/badge/status-active-success)

## Features

- 🎨 **Colorful Output**: Intuitive color-coded status indicators
- 🚀 **Fast**: Quick overview without scrolling through verbose Docker output
- 🔍 **Smart Detection**: Automatically finds and parses your compose file
- 🖥️ **Cross-Platform**: Works on Linux, macOS, and Windows
- 📦 **Simple**: Single Python script, easy to install and use

## Installation

### Prerequisites

- Python 3.7 or higher
- Docker and Docker Compose installed
- A `compose.yaml` or `docker-compose.yaml` file

### Quick Install

1. Clone this repository:
   ```bash
   git clone https://github.com/cdhouch/compose-status.git
   cd compose-status
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Make the script executable (Linux/macOS):
   ```bash
   chmod +x compose-status.py
   ```

4. (Optional) Add to your PATH for global access:
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export PATH="$PATH:/path/to/compose-status"
   ```

## Usage

### Basic Usage

Simply run the script:

```bash
./compose-status.py
```

The script will automatically look for `~/compose.yaml` (or `~/docker-compose.yaml`).

### Custom Compose File Location

Set the `COMPOSE_FILE` environment variable to use a different compose file:

```bash
export COMPOSE_FILE=/path/to/your/compose.yaml
./compose-status.py
```

Or specify it inline:

```bash
COMPOSE_FILE=/path/to/your/compose.yaml ./compose-status.py
```

### Example Output

```
Docker Compose Status (from /home/user/compose.yaml)
────────────────────────────────────────────
  audiobookshelf         🟢 running
  calibre-web            🟢 running
  ddns-updater           🟢 running
  nginx-proxy-manager    🟢 running
  qbittorrentvpn         🟢 running
────────────────────────────────────────────
Tip: Run 'cd /home/user && docker compose ps -a' for full details.
```

## Status Indicators

| Icon | Color | Status | Meaning |
|------|-------|--------|---------|
| 🟢 | Green | `running` | Service is active and healthy |
| 🔴 | Red | `stopped` | Service is not running (exited/dead/stopped) |
| 🟦 | Cyan | `created` | Container exists but hasn't been started |
| ⚪ | Yellow | `not created` | Container doesn't exist in Docker |
| 🟡 | Yellow | `*` | Unknown or uncommon state |

## How It Works

1. **Locates Compose File**: Checks `COMPOSE_FILE` environment variable, then defaults to `~/compose.yaml`
2. **Extracts Services**: Parses the YAML file to find all service names
3. **Queries Docker**: Runs `docker compose ps -a` to get current service states
4. **Displays Status**: Shows a formatted, colorized report of all services

## Requirements

- `pyyaml>=6.0` - For parsing Docker Compose YAML files
- `rich>=13.0` - For beautiful terminal output and colors

Install with:
```bash
pip install pyyaml rich
```

## Troubleshooting

### "docker compose command not found"

Make sure Docker and Docker Compose are installed and in your PATH:
```bash
docker --version
docker compose version
```

### "Error: compose.yaml not found!"

The script looks for `~/compose.yaml` by default. Either:
- Create a compose file at that location, or
- Set the `COMPOSE_FILE` environment variable to point to your compose file

### Services show as "not created"

This means Docker doesn't have containers for those services. Try:
```bash
cd ~ && docker compose up -d
```

### Colors not showing

The script uses the `rich` library which automatically detects terminal capabilities. If colors aren't showing:
- Make sure you're running in a terminal (not redirected output)
- Check that your terminal supports ANSI colors
- Try setting `TERM=xterm-256color` if needed

## Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Follow the existing code style and add comments
4. **Test your changes**: Make sure the script still works correctly
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**: Describe your changes and why they're useful

### Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Make changes and test locally
4. Ensure code is well-commented for maintainability

### Code Style

- Follow PEP 8 Python style guidelines
- Add docstrings to all functions
- Include inline comments for complex logic
- Keep functions focused and single-purpose

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the need for a quick, visual way to check Docker Compose service status
- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Uses [PyYAML](https://github.com/yaml/pyyaml) for safe YAML parsing

## Roadmap

Potential future enhancements:

- [ ] Support for multiple compose files
- [ ] JSON output mode for scripting
- [ ] Filter services by status
- [ ] Show resource usage (CPU, memory)
- [ ] Auto-refresh mode
- [ ] Integration with Docker Compose V2 profiles

## Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Search existing [Issues](https://github.com/cdhouch/compose-status/issues)
3. Open a new issue with details about your problem

---

Made with ❤️ for the Docker community

