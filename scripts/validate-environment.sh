#!/bin/bash
# Kyros PoC Environment Validation Script
# Validates all required development tools are installed with correct versions

set +e  # Don't exit on errors, we want to check all tools
EXIT_CODE=0

echo "============================================"
echo "Kyros PoC Environment Validation"
echo "============================================"
echo ""

# Function to compare version numbers
version_ge() {
    # Returns 0 (success) if version1 >= version2
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# Check Node.js
echo "Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | sed 's/v//')
    NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d'.' -f1)
    echo "  Found: Node.js v$NODE_VERSION"

    if [ "$NODE_MAJOR" -ge 20 ]; then
        echo "  Status: ✅ PASS (requires v20+)"
    else
        echo "  Status: ❌ FAIL (found v$NODE_VERSION, requires v20+)"
        EXIT_CODE=1
    fi
else
    echo "  Found: Not installed"
    echo "  Status: ❌ FAIL (requires v20+)"
    EXIT_CODE=1
fi
echo ""

# Check npm
echo "Checking npm..."
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    NPM_MAJOR=$(echo "$NPM_VERSION" | cut -d'.' -f1)
    echo "  Found: npm $NPM_VERSION"

    if [ "$NPM_MAJOR" -ge 10 ]; then
        echo "  Status: ✅ PASS (requires v10+)"
    else
        echo "  Status: ❌ FAIL (found v$NPM_VERSION, requires v10+)"
        EXIT_CODE=1
    fi
else
    echo "  Found: Not installed"
    echo "  Status: ❌ FAIL (requires v10+)"
    EXIT_CODE=1
fi
echo ""

# Check Python
echo "Checking Python..."
PYTHON_CMD=""
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

if [ -n "$PYTHON_CMD" ]; then
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)
    echo "  Found: Python $PYTHON_VERSION ($PYTHON_CMD)"

    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
        echo "  Status: ✅ PASS (requires 3.11+)"
    else
        echo "  Status: ❌ FAIL (found $PYTHON_VERSION, requires 3.11+)"
        EXIT_CODE=1
    fi
else
    echo "  Found: Not installed"
    echo "  Status: ❌ FAIL (requires 3.11+)"
    EXIT_CODE=1
fi
echo ""

# Check Docker (informational only in containerized dev environment)
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    DOCKER_MAJOR=$(echo "$DOCKER_VERSION" | cut -d'.' -f1)
    echo "  Found: Docker $DOCKER_VERSION"

    if [ "$DOCKER_MAJOR" -ge 24 ]; then
        echo "  Status: ✅ PASS (requires v24+)"
    else
        echo "  Status: ⚠️  WARN (found v$DOCKER_VERSION, requires v24+ on host)"
    fi
else
    echo "  Found: Not installed (expected in containerized dev environment)"
    echo "  Status: ⚠️  INFO (Docker required on host system for deployment only)"
    echo "  Note: Development can proceed without Docker in container"
fi
echo ""

# Check Docker Compose (informational only in containerized dev environment)
echo "Checking Docker Compose..."
COMPOSE_CMD=""
COMPOSE_VERSION=""

# Try new style first (docker compose)
if command -v docker &> /dev/null; then
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        COMPOSE_VERSION=$(docker compose version | awk '{print $4}' | sed 's/v//')
    fi
fi

# Try old style if new style failed (docker-compose)
if [ -z "$COMPOSE_VERSION" ] && command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | sed 's/,//' | sed 's/v//')
fi

if [ -n "$COMPOSE_VERSION" ]; then
    COMPOSE_MAJOR=$(echo "$COMPOSE_VERSION" | cut -d'.' -f1)
    COMPOSE_MINOR=$(echo "$COMPOSE_VERSION" | cut -d'.' -f2)
    echo "  Found: Docker Compose $COMPOSE_VERSION ($COMPOSE_CMD)"

    if [ "$COMPOSE_MAJOR" -ge 2 ] && [ "$COMPOSE_MINOR" -ge 29 ]; then
        echo "  Status: ✅ PASS (requires v2.29+)"
    else
        echo "  Status: ⚠️  WARN (found v$COMPOSE_VERSION, requires v2.29+ on host)"
    fi
else
    echo "  Found: Not installed (expected in containerized dev environment)"
    echo "  Status: ⚠️  INFO (Docker Compose required on host system for deployment only)"
    echo "  Note: Development can proceed without Docker Compose in container"
fi
echo ""

# Check git
echo "Checking git..."
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | awk '{print $3}')
    echo "  Found: git $GIT_VERSION"
    echo "  Status: ✅ PASS (any version acceptable)"
else
    echo "  Found: Not installed"
    echo "  Status: ❌ FAIL (git is required)"
    EXIT_CODE=1
fi
echo ""

# Summary
echo "============================================"
echo "Validation Summary"
echo "============================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All development prerequisites met! Ready for Epic 1."
    echo ""
    echo "Note: Docker/Docker Compose are not available in this containerized"
    echo "      development environment. They are only required on the host system"
    echo "      for deployment with 'docker-compose up'."
else
    echo "❌ Some development prerequisites missing or outdated."
    echo ""
    echo "Please install/upgrade the failed tools and run this script again."
    echo "See docs/environment-setup.md for installation instructions."
    echo ""
    echo "Note: Docker/Docker Compose warnings are informational only if running"
    echo "      inside a container. Development can proceed without them."
fi
echo ""

exit $EXIT_CODE
