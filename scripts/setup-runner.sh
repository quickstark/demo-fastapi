#!/bin/bash

# GitHub Runner Setup Script for Ubuntu
# This script helps configure and manage the self-hosted GitHub runner

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.runner.yml"
ENV_FILE=".env.runner"
ENV_EXAMPLE="runner.env.example"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_requirements() {
    print_header "Checking Requirements"
    
    # Check Docker
    if command -v docker &> /dev/null; then
        print_success "Docker installed: $(docker --version)"
        
        # Check Docker daemon
        if docker ps &> /dev/null; then
            print_success "Docker daemon is running"
        else
            print_error "Docker daemon is not accessible"
            echo "Please ensure Docker is running and you have permissions"
            exit 1
        fi
    else
        print_error "Docker is not installed"
        echo "Please install Docker first: https://docs.docker.com/engine/install/ubuntu/"
        exit 1
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose installed: $(docker-compose --version)"
    elif docker compose version &> /dev/null; then
        print_success "Docker Compose (plugin) installed: $(docker compose version)"
        COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose is not installed"
        echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Get Docker group ID
    DOCKER_GID=$(getent group docker | cut -d: -f3)
    print_success "Docker group ID: $DOCKER_GID"
    
    # Show Docker group members
    DOCKER_MEMBERS=$(getent group docker | cut -d: -f4)
    if [ ! -z "$DOCKER_MEMBERS" ]; then
        print_success "Docker group members: $DOCKER_MEMBERS"
    fi
    
    # Check if current user is in docker group
    if groups | grep -q docker; then
        print_success "Current user is in docker group"
    else
        print_warning "Current user is not in docker group"
        echo "You may need to run: sudo usermod -aG docker $USER"
    fi
}

setup_environment() {
    print_header "Setting Up Environment"
    
    # Check if env file exists
    if [ -f "$ENV_FILE" ]; then
        print_warning "Environment file $ENV_FILE already exists"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_success "Keeping existing environment file"
            return
        fi
    fi
    
    # Copy example env file
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        print_success "Created $ENV_FILE from $ENV_EXAMPLE"
    else
        print_error "$ENV_EXAMPLE not found"
        exit 1
    fi
    
    # Get GitHub token from existing compose (if available)
    if [ -f "docker-compose.yml" ] && grep -q "ACCESS_TOKEN:" docker-compose.yml; then
        EXISTING_TOKEN=$(grep "ACCESS_TOKEN:" docker-compose.yml | awk '{print $2}')
        if [ ! -z "$EXISTING_TOKEN" ]; then
            print_warning "Found existing GitHub token in docker-compose.yml"
            read -p "Use this token? (Y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                sed -i "s/GITHUB_ACCESS_TOKEN=.*/GITHUB_ACCESS_TOKEN=$EXISTING_TOKEN/" "$ENV_FILE"
                print_success "Updated GitHub token in $ENV_FILE"
            fi
        fi
    else
        print_warning "Please edit $ENV_FILE and add your GitHub Personal Access Token"
        echo "Create a token at: https://github.com/settings/tokens"
        echo "Required scopes: repo (full control of private repositories)"
    fi
    
    # Update Docker group ID
    sed -i "s/DOCKER_GROUP_ID=.*/DOCKER_GROUP_ID=$DOCKER_GID/" "$ENV_FILE"
    print_success "Updated Docker group ID to $DOCKER_GID"
    
    echo
    print_warning "Please review and update $ENV_FILE before starting the runner"
}

start_runner() {
    print_header "Starting GitHub Runner"
    
    # Check if env file exists
    if [ ! -f "$ENV_FILE" ]; then
        print_error "$ENV_FILE not found. Please run setup first."
        exit 1
    fi
    
    # Check if token is configured
    if grep -q "github_pat_your_token_here" "$ENV_FILE"; then
        print_error "GitHub token not configured in $ENV_FILE"
        echo "Please add your GitHub Personal Access Token"
        exit 1
    fi
    
    # Start runner
    ${COMPOSE_CMD:-docker-compose} -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    print_success "GitHub Runner started"
    echo
    echo "Check status with: ${COMPOSE_CMD:-docker-compose} -f $COMPOSE_FILE ps"
    echo "View logs with: ${COMPOSE_CMD:-docker-compose} -f $COMPOSE_FILE logs -f"
}

stop_runner() {
    print_header "Stopping GitHub Runner"
    
    ${COMPOSE_CMD:-docker-compose} -f "$COMPOSE_FILE" down
    print_success "GitHub Runner stopped"
}

status_runner() {
    print_header "GitHub Runner Status"
    
    ${COMPOSE_CMD:-docker-compose} -f "$COMPOSE_FILE" ps
    
    echo
    echo "Recent logs:"
    ${COMPOSE_CMD:-docker-compose} -f "$COMPOSE_FILE" logs --tail=20
}

restart_runner() {
    print_header "Restarting GitHub Runner"
    
    stop_runner
    sleep 2
    start_runner
}

logs_runner() {
    print_header "GitHub Runner Logs"
    
    ${COMPOSE_CMD:-docker-compose} -f "$COMPOSE_FILE" logs -f
}

test_docker_access() {
    print_header "Testing Docker Access from Runner"
    
    # Check if runner is running
    if ! ${COMPOSE_CMD:-docker-compose} -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        print_error "Runner is not running. Please start it first."
        exit 1
    fi
    
    echo "Testing Docker access from within the runner container..."
    ${COMPOSE_CMD:-docker-compose} -f "$COMPOSE_FILE" exec runner docker version
    
    if [ $? -eq 0 ]; then
        print_success "Docker is accessible from the runner!"
        echo
        echo "Testing Docker operations..."
        ${COMPOSE_CMD:-docker-compose} -f "$COMPOSE_FILE" exec runner docker run --rm hello-world
    else
        print_error "Docker is not accessible from the runner"
        echo "Check that /var/run/docker.sock is properly mounted"
    fi
}

update_runner() {
    print_header "Updating GitHub Runner"
    
    echo "Pulling latest runner image..."
    ${COMPOSE_CMD:-docker-compose} -f "$COMPOSE_FILE" pull
    
    print_success "Runner image updated"
    echo "Restart the runner to use the new image: $0 restart"
}

# Main menu
show_menu() {
    echo
    print_header "GitHub Runner Management"
    echo "1) Check requirements"
    echo "2) Setup environment"
    echo "3) Start runner"
    echo "4) Stop runner"
    echo "5) Restart runner"
    echo "6) Show status"
    echo "7) View logs"
    echo "8) Test Docker access"
    echo "9) Update runner image"
    echo "0) Exit"
    echo
    read -p "Select an option: " choice
    
    case $choice in
        1) check_requirements ;;
        2) setup_environment ;;
        3) start_runner ;;
        4) stop_runner ;;
        5) restart_runner ;;
        6) status_runner ;;
        7) logs_runner ;;
        8) test_docker_access ;;
        9) update_runner ;;
        0) exit 0 ;;
        *) print_error "Invalid option" ;;
    esac
}

# Handle command line arguments
case "${1:-}" in
    check)
        check_requirements
        ;;
    setup)
        check_requirements
        setup_environment
        ;;
    start)
        start_runner
        ;;
    stop)
        stop_runner
        ;;
    restart)
        restart_runner
        ;;
    status)
        status_runner
        ;;
    logs)
        logs_runner
        ;;
    test)
        test_docker_access
        ;;
    update)
        update_runner
        ;;
    *)
        # Interactive menu
        while true; do
            show_menu
        done
        ;;
esac
