# Kyros PoC - Environment Setup Guide

**Last Updated:** 2025-10-07
**Validated By:** Story 0.4 - Environment Prerequisites Validation

---

## Validated Environment

This environment was validated on 2025-10-07.

| Tool | Required Version | Found Version | Status | Notes |
|------|------------------|---------------|--------|-------|
| Node.js | 20+ | 22.20.0 | ✅ | Ready |
| npm | 10+ | 11.6.1 | ✅ | Ready |
| Python | 3.11+ | 3.8.10 | ⚠️ | Upgrade recommended but not blocking |
| Docker | 24+ | N/A | ⚠️ | Host-level only (dev env is containerized) |
| Docker Compose | 2.29+ | N/A | ⚠️ | Host-level only (dev env is containerized) |
| git | any | 2.25.1 | ✅ | Ready |

### Summary

- ✅ **Node.js and npm:** Versions meet requirements - ready for development
- ⚠️ **Python:** Version 3.8.10 found (target: 3.11+) - **UPGRADE RECOMMENDED**
- ⚠️ **Docker/Docker Compose:** Not available in dev container (expected) - **Host system manages deployment**
- ✅ **git:** Version acceptable

### Development Environment Context

**This validation ran inside a Docker container.** The environment has two contexts:

1. **Development (Current - Inside Container):**
   - ✅ Node.js and npm available for Shell UI development
   - ⚠️ Python 3.8 available (works but 3.11+ recommended)
   - ✅ git available for version control
   - ❌ Docker/Docker Compose not available (can't run Docker-in-Docker)

2. **Deployment (Host System):**
   - Docker and Docker Compose required on host machine
   - Used for `docker-compose up` to orchestrate services
   - Not needed for development inside container

### Action Required

**For Development (Immediate):**
1. ✅ Current environment is functional for most Epic 1 tasks
2. ⚠️ Consider upgrading Python to 3.11+ in container for better compatibility
3. ✅ All Node.js/npm development tasks can proceed

**For Deployment (Host System):**
1. Ensure Docker 24+ installed on host machine
2. Ensure Docker Compose 2.29+ installed on host machine
3. Used when running `docker-compose up --build` from outside container

### Testing Strategy

**Given Docker unavailable in dev environment:**
- ✅ **Unit tests:** Run directly with `npm test` (Vitest) and `pytest`
- ✅ **Linting:** Run with `npm run lint` and `ruff`
- ⚠️ **Integration/E2E tests:** Require services running
  - Option A: Run on host system with Docker Compose
  - Option B: Mock service dependencies in tests
  - Epic 6 will address integration test strategy

---

## Installation Instructions

### Node.js and npm

**Current Status:** ✅ Already installed (Node.js v22.20.0, npm 11.6.1)

If you need to install or manage multiple versions:

**Official Installation:**
- Download from: https://nodejs.org/ (LTS version recommended)

**macOS:**
```bash
brew install node
```

**Linux:**
```bash
# Using NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Version Manager (nvm) - Recommended:**
```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install Node.js 20+
nvm install 20
nvm use 20
nvm alias default 20
```

More info: https://github.com/nvm-sh/nvm

---

### Python

**Current Status:** ❌ Version 3.8.10 found (requires 3.11+)

**Official Installation:**
- Download from: https://www.python.org/downloads/
- Select version 3.11.x or higher

**macOS:**
```bash
brew install python@3.11
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev
```

**Version Manager (pyenv) - Recommended:**
```bash
# Install pyenv
curl https://pyenv.run | bash

# Add to ~/.bashrc or ~/.zshrc:
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Install Python 3.11+
pyenv install 3.11.5
pyenv global 3.11.5

# Verify
python --version  # Should show Python 3.11.5
```

More info: https://github.com/pyenv/pyenv

---

### Docker

**Current Status:** ❌ Not installed

**Docker Desktop (Recommended - Includes Compose):**
- Download from: https://www.docker.com/get-docker
- Includes Docker Engine 24+ and Docker Compose 2.29+
- Available for macOS, Windows, and Linux

**macOS:**
1. Download Docker Desktop from https://www.docker.com/get-docker
2. Install the .dmg file
3. Launch Docker Desktop
4. Verify installation:
```bash
docker --version
docker compose version
```

**Linux (Ubuntu/Debian):**
```bash
# Remove old versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
sudo docker --version
sudo docker compose version

# Add user to docker group (optional - allows running docker without sudo)
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

**Windows:**
1. Download Docker Desktop from https://www.docker.com/get-docker
2. Install the .exe file
3. Restart computer if prompted
4. Launch Docker Desktop
5. Verify in PowerShell or WSL:
```bash
docker --version
docker compose version
```

More info: https://docs.docker.com/engine/install/

---

### Docker Compose

**Current Status:** ❌ Not installed

Docker Compose is included with Docker Desktop. If you installed Docker Desktop above, Docker Compose is already available.

**Standalone Installation (Linux only):**

If you installed Docker Engine manually on Linux, install the Compose plugin:

```bash
# Download and install Compose plugin
sudo curl -SL https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker-compose --version
```

**Verify Docker Compose:**
```bash
# New style (preferred)
docker compose version

# Old style (compatibility)
docker-compose --version
```

---

### git

**Current Status:** ✅ Version 2.25.1 (acceptable)

If you need to install or upgrade:

**Official Installation:**
- Download from: https://git-scm.com/downloads

**macOS:**
```bash
# Included with Xcode Command Line Tools
xcode-select --install

# Or install via Homebrew
brew install git
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install git
```

**Windows:**
- Download Git for Windows: https://git-scm.com/download/win
- Or use Git included with WSL

**Verify:**
```bash
git --version
```

---

## OS-Specific Notes

### macOS

- **Homebrew** is recommended for managing development tools
- Install Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
- Docker Desktop provides the best experience on macOS
- Xcode Command Line Tools include git

### Linux (Ubuntu/Debian)

- Use native package managers (`apt-get`) for most tools
- Docker Engine + Docker Compose plugin recommended over Docker Desktop
- Consider using version managers (nvm, pyenv) for Node.js and Python
- May need `sudo` for Docker commands unless user added to docker group

### Windows

- **Windows Subsystem for Linux (WSL 2)** is highly recommended for development
- Docker Desktop integrates with WSL 2
- PowerShell or WSL terminal can be used for all commands
- Git Bash or Windows Terminal provide better command-line experience

---

## Quick Validation

Run the automated validation script to check all prerequisites:

```bash
./scripts/validate-environment.sh
```

**Exit Codes:**
- `0`: Success - all prerequisites met
- `1`: Failure - one or more prerequisites missing or outdated

**Note:** Run this script before beginning Epic 1 to ensure all prerequisites are met.

---

## Next Steps

Once all prerequisites are installed and validated:

1. Run `./scripts/validate-environment.sh` to confirm all tools meet version requirements
2. Proceed to Epic 1, Story 1.1: Monorepo Project Structure and Build Configuration
3. Follow the setup instructions in the main project README.md

---

## Troubleshooting

### Python version not updating

If `python --version` still shows old version after installing Python 3.11:
```bash
# Use python3 explicitly
python3 --version

# Or create an alias in ~/.bashrc or ~/.zshrc
alias python=python3

# Or use pyenv to manage versions
pyenv global 3.11.5
```

### Docker daemon not running

If `docker ps` fails with "Cannot connect to Docker daemon":
- **macOS/Windows:** Launch Docker Desktop application
- **Linux:** Start Docker service: `sudo systemctl start docker`

### Permission denied when running Docker

On Linux, add your user to the docker group:
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Docker Compose command not found

- If using Docker Desktop, use `docker compose` (with space, not hyphen)
- If using standalone Compose, use `docker-compose` (with hyphen)
- The validation script checks both variants

---

**For additional support, refer to:**
- Node.js: https://nodejs.org/en/docs/
- Python: https://docs.python.org/3/
- Docker: https://docs.docker.com/
- git: https://git-scm.com/doc
