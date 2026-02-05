# Monopoly Agents — Podman Setup Guide

Podman is a drop-in replacement for Docker. All existing Docker scripts work with a simple alias.

## Install Podman

```bash
# macOS
brew install podman
podman machine init --memory 4096 --disk_size 100
podman machine start

# Linux (Debian/Ubuntu)
sudo apt-get install -y podman

# Linux (Fedora/RHEL)
sudo dnf install -y podman
```

## Usage

### Option 1: Alias Docker (use existing scripts)

```bash
alias docker=podman
./scripts/bash/build-docker.sh
./scripts/bash/run-docker-dev.sh
```

### Option 2: Direct Podman commands

```bash
podman build -t monopoly-agents:latest .

# Interactive dev
podman run -it \
  -v $(pwd):/home -v $(pwd)/.env:/home/.env \
  -e PYTHONPATH=. monopoly-agents:latest /bin/bash

# Run CLI command
podman run --rm \
  -v $(pwd):/home -v $(pwd)/.env:/home/.env \
  -e PYTHONPATH=. monopoly-agents:latest \
  python scripts/python/cli.py get-all-markets --limit 5

# Run API server
podman run -it -p 8000:8000 \
  -v $(pwd):/home -v $(pwd)/.env:/home/.env \
  -e PYTHONPATH=. monopoly-agents:latest \
  python scripts/python/server.py
```

## Container Management

```bash
podman ps -a              # List containers
podman logs <container>   # View logs
podman exec -it <container> bash  # Shell into container
podman stop <container>   # Stop
podman rm <container>     # Remove
```

## Troubleshooting

**"Cannot connect to Podman"** — Start the podman machine:
```bash
podman machine start
```

**"Permission denied" on volume mounts:**
```bash
podman run --userns=host ...
```

**Container exits immediately** — Check logs:
```bash
podman logs <container_id>
```

**Out of disk space:**
```bash
podman image prune -a
podman container prune
podman volume prune
```
