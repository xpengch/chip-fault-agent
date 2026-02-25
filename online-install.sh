#!/bin/bash

set -e

echo "=========================================="
echo "  Chip Fault AI - Online Installation"
echo "=========================================="
echo ""
echo "This script will install the Chip Fault AI Agent"
echo "system with automatic dependency download."
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -e "[Check] Python environment..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python not installed!${NC}"
    echo ""
    echo "Please install Python 3.12+ from:"
    echo "https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}[OK] Python $PYTHON_VERSION detected${NC}"
echo ""

# Check Git
echo -e "[Check] Git..."
if ! command -v git &> /dev/null; then
    echo -e "${RED}[ERROR] Git not installed!${NC}"
    echo ""
    echo "Please install Git:"
    echo "  Ubuntu/Debian: sudo apt-get install git"
    echo "  CentOS/RHEL:   sudo yum install git"
    echo "  macOS:         brew install git"
    exit 1
fi

GIT_VERSION=$(git --version 2>&1 | awk '{print $3}')
echo -e "${GREEN}[OK] Git $GIT_VERSION detected${NC}"
echo ""

# Check Docker (optional)
echo -e "[Check] Docker (optional for full deployment)..."
if command -v docker &> /dev/null; then
    echo -e "${GREEN}[OK] Docker detected${NC}"
    DOCKER_AVAILABLE=1

    if docker compose version &> /dev/null; then
        echo -e "${GREEN}[OK] Docker Compose available${NC}"
        DOCKER_COMPOSE_AVAILABLE=1
    else
        echo -e "${YELLOW}[WARNING] Docker Compose not available${NC}"
        DOCKER_COMPOSE_AVAILABLE=0
    fi
else
    echo -e "${YELLOW}[WARNING] Docker not installed${NC}"
    echo "         You can still use development mode"
    DOCKER_AVAILABLE=0
fi
echo ""

# Ask installation mode
echo "=========================================="
echo "  Select Installation Mode"
echo "=========================================="
echo ""
echo "1. Quick Start (Docker) - Recommended for production"
echo "   - Install all services with Docker"
echo "   - Requires Docker & Docker Compose"
echo ""
echo "2. Development Mode - For developers"
echo "   - Install dependencies locally"
echo "   - Run services manually"
echo ""
echo "3. Minimal Mode - Backend only"
echo "   - Install Python dependencies only"
echo ""
read -p "Select mode (1/2/3): " MODE

case $MODE in
    1)
        if [ "$DOCKER_AVAILABLE" -eq 0 ]; then
            echo -e "${RED}[ERROR] Docker mode selected but Docker not available!${NC}"
            echo "       Please install Docker first"
            exit 1
        fi
        docker_install
        ;;
    2)
        dev_install
        ;;
    3)
        minimal_install
        ;;
    *)
        echo -e "${RED}[ERROR] Invalid selection${NC}"
        exit 1
        ;;
esac

docker_install() {
    echo ""
    echo "=========================================="
    echo "  Docker Installation"
    echo "=========================================="
    echo ""

    # Clone or update repository
    if [ -d .git ]; then
        echo "[INFO] Repository already exists"
        read -p "Update repository? (y/n): " UPDATE
        if [ "$UPDATE" = "y" ] || [ "$UPDATE" = "Y" ]; then
            echo "[1/5] Updating repository..."
            git pull origin master
        fi
    else
        echo "[1/5] Cloning repository..."
        git clone https://github.com/xpengch/chip-fault-agent.git
        cd chip_fault_agent
    fi

    echo -e "${GREEN}[OK] Repository ready${NC}"
    echo ""

    # Check BGE model
    echo "[2/5] Checking BGE model..."
    if [ ! -d "bge-model" ]; then
        echo "BGE model will be downloaded on first run"
        echo "Run download-bge.py to download it now (optional)"
    else
        echo -e "${GREEN}[OK] BGE model found${NC}"
    fi
    echo ""

    # Configure environment
    echo "[3/5] Configuring environment..."
    if [ ! -f .env ]; then
        if [ -f .env.docker.template ]; then
            cp .env.docker.template .env
            echo ""
            echo -e "${YELLOW}[IMPORTANT] Please edit .env file and set:${NC}"
            echo "              - ANTHROPIC_API_KEY"
            echo ""
            ${EDITOR:-nano} .env
            read -p "Press Enter after configuration..."
        else
            echo -e "${YELLOW}[WARNING] .env.docker.template not found${NC}"
            echo "         Creating basic .env file..."
            echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
            echo "Please edit .env and set your API key"
            ${EDITOR:-nano} .env
        fi
    else
        echo -e "${GREEN}[OK] .env file exists${NC}"
    fi
    echo ""

    # Build Docker images
    echo "[4/5] Building Docker images..."
    docker compose build
    echo -e "${GREEN}[OK] Docker images ready${NC}"
    echo ""

    # Start services
    echo "[5/5] Starting services..."
    docker compose up -d
    echo -e "${GREEN}[OK] Services started${NC}"
    echo ""

    # Wait for services
    echo "Waiting for services to be ready..."
    sleep 30

    if curl -s http://localhost:8889/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}[OK] Backend service ready${NC}"
    else
        echo -e "${YELLOW}[WARNING] Backend service may not be fully ready${NC}"
        echo "         Check logs: docker compose logs -f"
    fi
    echo ""

    success
}

dev_install() {
    echo ""
    echo "=========================================="
    echo "  Development Installation"
    echo "=========================================="
    echo ""

    # Check if in repository
    if [ ! -d .git ]; then
        echo "[1/6] Cloning repository..."
        git clone https://github.com/xpengch/chip-fault-agent.git
        cd chip_fault_agent
    fi

    echo "[2/6] Creating virtual environment..."
    if [ ! -d venv ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    echo -e "${GREEN}[OK] Virtual environment created${NC}"
    echo ""

    echo "[3/6] Installing Python dependencies..."
    python -m pip install --upgrade pip -q
    pip install -r requirements.txt
    echo -e "${GREEN}[OK] Dependencies installed${NC}"
    echo ""

    echo "[4/6] Downloading BGE model..."
    python scripts/init_bge_model.py
    echo -e "${GREEN}[OK] BGE model initialized${NC}"
    echo ""

    echo "[5/6] Configuring environment..."
    if [ ! -f .env ]; then
        if [ -f .env.docker.template ]; then
            cp .env.docker.template .env
        else
            cat > .env << EOF
ANTHROPIC_API_KEY=your_api_key_here
POSTGRES_HOST=localhost
NEO4J_URI=bolt://localhost:7687
REDIS_HOST=localhost
EOF
        fi
        echo ""
        echo -e "${YELLOW}[IMPORTANT] Please edit .env file and set your API keys${NC}"
        ${EDITOR:-nano} .env
    fi
    echo -e "${GREEN}[OK] Environment configured${NC}"
    echo ""

    echo "[6/6] Installing frontend dependencies..."
    cd frontend-v2
    npm install
    echo -e "${GREEN}[OK] Frontend dependencies installed${NC}"
    cd ..
    echo ""

    echo "=========================================="
    echo "  Development Setup Complete!"
    echo "=========================================="
    echo ""
    echo "To start the development servers:"
    echo ""
    echo "1. Start databases (if using Docker):"
    echo "   docker compose up -d postgres neo4j redis"
    echo ""
    echo "2. Start backend (new terminal):"
    echo "   source venv/bin/activate"
    echo "   uvicorn src.api.app:app --host 0.0.0.0 --port 8889 --reload"
    echo ""
    echo "3. Start frontend (new terminal):"
    echo "   cd frontend-v2"
    echo "   npm run dev"
    echo ""
}

minimal_install() {
    echo ""
    echo "=========================================="
    echo "  Minimal Installation (Backend Only)"
    echo "=========================================="
    echo ""

    echo "[1/4] Creating virtual environment..."
    if [ ! -d venv ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    echo -e "${GREEN}[OK] Virtual environment created${NC}"
    echo ""

    echo "[2/4] Installing Python dependencies..."
    python -m pip install --upgrade pip -q
    pip install -r requirements.txt
    echo -e "${GREEN}[OK] Dependencies installed${NC}"
    echo ""

    echo "[3/4] Configuring environment..."
    if [ ! -f .env ]; then
        cat > .env << EOF
ANTHROPIC_API_KEY=your_api_key_here
POSTGRES_HOST=localhost
NEO4J_URI=bolt://localhost:7687
REDIS_HOST=localhost
EOF
        echo ""
        echo -e "${YELLOW}[IMPORTANT] Please edit .env file and set your API keys${NC}"
        ${EDITOR:-nano} .env
    fi
    echo -e "${GREEN}[OK] Environment configured${NC}"
    echo ""

    echo "[4/4] Initializing BGE model..."
    python scripts/init_bge_model.py
    echo -e "${GREEN}[OK] BGE model initialized${NC}"
    echo ""

    echo "=========================================="
    echo "  Minimal Installation Complete!"
    echo "=========================================="
    echo ""
    echo "To start the backend:"
    echo ""
    echo "1. Activate virtual environment:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Start the server:"
    echo "   uvicorn src.api.app:app --host 0.0.0.0 --port 8889"
    echo ""
}

success() {
    echo "=========================================="
    echo "  Installation Complete!"
    echo "=========================================="
    echo ""
    echo "Access URLs:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend:  http://localhost:8889"
    echo "  Docs:     http://localhost:8889/docs"
    echo ""
    echo "Common commands:"
    echo "  View logs: docker compose logs -f"
    echo "  Stop:     docker compose down"
    echo "  Restart:  docker compose restart"
    echo "  Status:   docker compose ps"
    echo ""
    echo "Documentation:"
    echo "  https://github.com/xpengch/chip-fault-agent"
    echo ""
}
