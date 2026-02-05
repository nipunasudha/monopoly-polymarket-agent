# Podman Setup Guide for Polymarket Agents

This guide provides instructions for running the Polymarket agents using Podman instead of Docker.

## Prerequisites

### Install Podman

#### macOS
```bash
# Using Homebrew
brew install podman

# Initialize podman machine (if first time)
podman machine init --memory 4096 --disk_size 100
podman machine start

# Verify installation
podman version
```

#### Linux (Fedora/RHEL)
```bash
sudo dnf install -y podman

# Verify installation
podman version
```

#### Linux (Debian/Ubuntu)
```bash
sudo apt-get install -y podman

# Verify installation
podman version
```

#### Windows (WSL2)
```powershell
wsl --install podman
# Or use Windows installer from podman.io
```

---

## Setup Options

### Option 1: Docker CLI Alias (Recommended for existing scripts)

If you want to use the existing `./scripts/bash/build-docker.sh` and `./scripts/bash/run-docker.sh` scripts with Podman:

```bash
# Create alias in your shell profile (~/.zshrc, ~/.bashrc, etc.)
alias docker=podman

# Or set it for current session only
export DOCKER_HOST=unix:///var/run/podman/podman.sock
```

Then run the existing scripts:
```bash
./scripts/bash/build-docker.sh
./scripts/bash/run-docker-dev.sh
```

### Option 2: Direct Podman Commands (Recommended for new workflows)

Build the image:
```bash
podman build -t polymarket-agents:latest .
```

Run in development mode:
```bash
podman run -it \
  --name polymarket-agent-dev \
  -v $(pwd):/home \
  -v $(pwd)/.env:/home/.env \
  -e PYTHONUNBUFFERED=1 \
  polymarket-agents:latest \
  /bin/bash
```

---

## Building with Podman

### Build Image
```bash
podman build -t polymarket-agents:latest .

# Verify image built successfully
podman images | grep polymarket
```

### Build with Custom Python Version
The Dockerfile uses Python 3.9. To build with a different Python:

```bash
podman build \
  --build-arg PYTHON_VERSION=3.10 \
  -t polymarket-agents:python3.10 .
```

---

## Running Containers

### Development Container (Interactive)
```bash
podman run -it \
  --name polymarket-agent-dev \
  -v $(pwd):/home \
  -v $(pwd)/.env:/home/.env \
  -e PYTHONUNBUFFERED=1 \
  -e PYTHONPATH=. \
  polymarket-agents:latest \
  /bin/bash
```

**Inside the container:**
```bash
cd /home
python scripts/python/cli.py --help
python scripts/python/cli.py get-all-markets --limit 3
```

### Production Container (Daemon)
```bash
podman run -d \
  --name polymarket-agent-prod \
  -v $(pwd)/.env:/home/.env:ro \
  -e PYTHONPATH=. \
  --restart=always \
  polymarket-agents:latest \
  python scripts/python/server.py
```

### Run with FastAPI Server
```bash
podman run -it \
  -p 8000:8000 \
  -v $(pwd):/home \
  -v $(pwd)/.env:/home/.env \
  -e PYTHONPATH=. \
  polymarket-agents:latest \
  python scripts/python/server.py
```

Access API at: http://localhost:8000

### Run with CLI Command
```bash
podman run --rm \
  -v $(pwd):/home \
  -v $(pwd)/.env:/home/.env \
  -e PYTHONPATH=. \
  polymarket-agents:latest \
  python scripts/python/cli.py get-all-markets --limit 5
```

---

## Container Management

### List Running Containers
```bash
podman ps
podman ps -a  # Include stopped containers
```

### View Container Logs
```bash
podman logs polymarket-agent-dev

# Follow logs in real-time
podman logs -f polymarket-agent-dev
```

### Execute Commands in Running Container
```bash
podman exec -it polymarket-agent-dev bash

# Or run a single command
podman exec polymarket-agent-dev python scripts/python/cli.py get-all-markets --limit 3
```

### Stop Container
```bash
podman stop polymarket-agent-dev
```

### Remove Container
```bash
podman rm polymarket-agent-dev

# Force remove if running
podman rm -f polymarket-agent-dev
```

### Remove Image
```bash
podman rmi polymarket-agents:latest
```

---

## Pod Management

### Create a Pod (Advanced)
```bash
# Create pod with multiple containers
podman pod create --name polymarket-pod -p 8000:8000

# Run CLI in pod
podman run --pod polymarket-pod \
  -v $(pwd):/home \
  polymarket-agents:latest

# Run API in pod
podman run --pod polymarket-pod \
  -p 8000:8000 \
  polymarket-agents:latest \
  python scripts/python/server.py
```

### List Pods
```bash
podman pod ps
```

### Remove Pod
```bash
podman pod rm polymarket-pod
```

---

## Volume Mounts

### Bind Mount (Direct file access)
```bash
podman run -it \
  -v $(pwd):/home \
  polymarket-agents:latest
```

### Named Volume (Persistent data)
```bash
# Create volume
podman volume create polymarket-data

# Run with volume
podman run -it \
  -v polymarket-data:/data \
  polymarket-agents:latest

# List volumes
podman volume ls

# Inspect volume
podman volume inspect polymarket-data

# Remove volume
podman volume rm polymarket-data
```

### Read-only Mount
```bash
podman run -it \
  -v $(pwd)/.env:/home/.env:ro \
  polymarket-agents:latest
```

---

## Environment Variables

### Pass Environment Variables
```bash
# Via -e flag
podman run -e OPENAI_API_KEY="sk-..." \
  -e POLYGON_WALLET_PRIVATE_KEY="0x..." \
  polymarket-agents:latest

# Via --env-file
podman run --env-file .env \
  polymarket-agents:latest

# Via .env file mount
podman run -v $(pwd)/.env:/home/.env \
  polymarket-agents:latest
```

---

## Networking

### Expose Ports
```bash
# Map port 8000
podman run -p 8000:8000 \
  polymarket-agents:latest \
  python scripts/python/server.py

# Map multiple ports
podman run -p 8000:8000 -p 9000:9000 \
  polymarket-agents:latest

# Map to different host port
podman run -p 127.0.0.1:3000:8000 \
  polymarket-agents:latest
```

### Network Modes
```bash
# Host network (use host's network)
podman run --network host \
  polymarket-agents:latest

# Container networking (default)
podman run --network bridge \
  polymarket-agents:latest
```

---

## Podman Compose (Multi-container)

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  polymarket-api:
    build: .
    command: python scripts/python/server.py
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=.
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - POLYGON_WALLET_PRIVATE_KEY=${POLYGON_WALLET_PRIVATE_KEY}
    volumes:
      - .:/home
      - ./.env:/home/.env

  polymarket-cli:
    build: .
    environment:
      - PYTHONPATH=.
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - .:/home
    stdin_open: true
    tty: true
```

Run with compose:
```bash
podman-compose up
podman-compose down
podman-compose logs -f polymarket-api
```

---

## Troubleshooting

### Issue: "Cannot connect to Podman"
**Solution:**
```bash
# Start podman daemon/machine
podman machine start

# Or check socket
podman info
```

### Issue: "Permission denied" on volume mounts
**Solution:**
```bash
# Run with user namespace
podman run --userns=host ...

# Or change file permissions
sudo chown 1000:1000 $(pwd)
```

### Issue: Container exits immediately
**Solution:**
```bash
# Check logs
podman logs <container_id>

# Run with -it for interactive debugging
podman run -it <image> /bin/bash
```

### Issue: Out of disk space
**Solution:**
```bash
# Prune unused images/containers/volumes
podman image prune -a
podman container prune
podman volume prune

# Check disk usage
podman system df
```

### Issue: Network access from container
**Solution:**
```bash
# Use host network
podman run --network host ...

# Or debug networking
podman run --rm --network host alpine ping 8.8.8.8
```

---

## Podman vs Docker

| Feature | Podman | Docker |
|---------|--------|--------|
| Daemon | Daemonless (podman CLI) | Daemon required |
| Root privileges | Optional | Usually required |
| Rootless containers | Yes, by default | Requires configuration |
| Kubernetes integration | Native podman-kube | Via Docker Desktop |
| Compose | podman-compose | docker-compose |
| Performance | Slightly lighter | Standard benchmark |
| Compatibility | Docker-compatible | Native (original) |

---

## Common Commands Cheatsheet

```bash
# Build
podman build -t polymarket-agents:latest .

# Run interactive
podman run -it -v $(pwd):/home polymarket-agents:latest /bin/bash

# Run with env file
podman run --env-file .env polymarket-agents:latest

# List images
podman images

# List containers
podman ps -a

# View logs
podman logs <container>

# Execute command
podman exec -it <container> bash

# Stop/remove
podman stop <container>
podman rm <container>

# Remove image
podman rmi polymarket-agents:latest
```

---

## Next Steps

1. **Test the setup:**
   ```bash
   podman run --rm polymarket-agents:latest python -c "import agents; print('✓ Works!')"
   ```

2. **Configure API keys:**
   ```bash
   podman run --env-file .env polymarket-agents:latest python scripts/python/cli.py get-all-markets
   ```

3. **Run the server:**
   ```bash
   podman run -p 8000:8000 --env-file .env polymarket-agents:latest python scripts/python/server.py
   ```

---

## Additional Resources

- [Podman Documentation](https://docs.podman.io/)
- [Podman Compose](https://github.com/containers/podman-compose)
- [Container Best Practices](https://docs.podman.io/en/latest/markdown/podman-run.1.html)
- [Podman vs Docker](https://docs.podman.io/en/latest/Introduction.html)

---

**Last Updated:** February 6, 2026
**Podman Version:** Compatible with 3.x+
**Status:** ✓ Ready for Production
