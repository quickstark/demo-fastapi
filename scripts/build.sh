#!/bin/bash

# Parse command line arguments
USE_CACHE=true
BUILD_LOCAL=false
CLEAN_CONTAINERS=false
RUN_CONTAINER=false
CONTAINER_NAME="images"
PORT="9000:8080"
PGHOST="host.docker.internal"
USE_PODMAN=false
USE_RANCHER=false
ENV_FILE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --no-cache)
      USE_CACHE=false
      shift
      ;;
    --local)
      BUILD_LOCAL=true
      shift
      ;;
    --clean)
      CLEAN_CONTAINERS=true
      shift
      ;;
    --run)
      RUN_CONTAINER=true
      shift
      ;;
    --podman)
      USE_PODMAN=true
      BUILD_LOCAL=true  # We want local behavior but with podman
      shift
      ;;
    --rancher)
      USE_RANCHER=true
      BUILD_LOCAL=true  # We want local behavior but with rancher
      shift
      ;;
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--no-cache] [--local] [--clean] [--run] [--podman] [--rancher] [--env-file <file>]"
      echo "  --no-cache       : Build without using Docker cache"
      echo "  --local          : Build for local testing instead of Synology"
      echo "  --clean          : Remove existing containers named '${CONTAINER_NAME}'"
      echo "  --run            : Start a container after build (implies --local, removes existing container)"
      echo "  --podman         : Build for Podman instead of Docker"
      echo "  --rancher        : Build for Rancher Desktop with containerd/nerdctl"
      echo "  --env-file <file>: Load environment variables from file (for --run)"
      exit 1
      ;;
  esac
done

# If --run is specified, ensure --local is also set
if [ "$RUN_CONTAINER" = true ]; then
  BUILD_LOCAL=true
  # When running, we always want to clean existing containers with the same name
  CLEAN_CONTAINERS=true
fi

# Configuration
IMAGE_NAME="images-api"
IMAGE_TAG="latest"
DESKTOP_PATH="$HOME/Desktop"
OUTPUT_FILE="$DESKTOP_PATH/${IMAGE_NAME}.tar"
PLATFORM="linux/amd64"  # AMD Ryzen R1600 is x86_64/AMD64 architecture

# Set container runtime command
if [ "$USE_RANCHER" = true ]; then
  CONTAINER_CMD="nerdctl"
  PGHOST="host.rancher-desktop.internal"  # Rancher Desktop's host gateway
elif [ "$USE_PODMAN" = true ]; then
  CONTAINER_CMD="podman"
else
  CONTAINER_CMD="docker"
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${CYAN}================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}================================${NC}"
    echo
}

print_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if container exists
container_exists() {
  ${CONTAINER_CMD} ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"
  return $?
}

# Function to check if container is running
container_running() {
  ${CONTAINER_CMD} ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"
  return $?
}

# Function to load and validate environment file
load_env_file() {
    local env_file="$1"
    
    if [[ -z "$env_file" ]]; then
        # Check for default .env file
        if [[ -f ".env" ]]; then
            env_file=".env"
            print_step "Using default .env file"
        else
            print_warning "No environment file specified and .env not found"
            print_warning "Container will use Dockerfile defaults"
            return 1
        fi
    fi
    
    if [[ ! -f "$env_file" ]]; then
        print_error "Environment file '$env_file' not found"
        exit 1
    fi
    
    print_step "Loading environment from: $env_file"
    
    # Count total variables and placeholders
    local total_vars=0
    local placeholder_vars=0
    local empty_vars=0
    local key_vars=()
    
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip empty lines and comments
        if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        
        if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
            local key="${BASH_REMATCH[1]}"
            local value="${BASH_REMATCH[2]}"
            
            # Remove quotes
            value=$(echo "$value" | sed 's/^["'\'']\|["'\'']$//g')
            
            key_vars+=("$key")
            ((total_vars++))
            
            if [[ -z "$value" ]]; then
                ((empty_vars++))
            elif [[ "$value" =~ ^(your-|sk-your-|secret_your-) ]]; then
                ((placeholder_vars++))
            fi
        fi
    done < "$env_file"
    
    echo -e "${CYAN}Environment Summary:${NC}"
    echo -e "  Total variables: $total_vars"
    echo -e "  Valid values: $((total_vars - placeholder_vars - empty_vars))"
    echo -e "  Placeholder values: $placeholder_vars"
    echo -e "  Empty values: $empty_vars"
    
    # Highlight key observability settings
    local obs_provider=$(grep "^OBSERVABILITY_PROVIDER=" "$env_file" 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "not set")
    local sentry_dsn=$(grep "^SENTRY_DSN=" "$env_file" 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "")
    local dd_agent=$(grep "^DD_AGENT_HOST=" "$env_file" 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "not set")
    
    echo -e "${CYAN}Observability Configuration:${NC}"
    echo -e "  Provider: ${obs_provider}"
    if [[ "$obs_provider" == "sentry" || "$obs_provider" == "\"sentry\"" ]]; then
        if [[ -n "$sentry_dsn" && "$sentry_dsn" != "not set" ]]; then
            echo -e "  Sentry DSN: ${GREEN}configured${NC}"
        else
            echo -e "  Sentry DSN: ${RED}MISSING${NC}"
        fi
    elif [[ "$obs_provider" == "datadog" || "$obs_provider" == "\"datadog\"" ]]; then
        echo -e "  Datadog Agent: ${dd_agent}"
    fi
    echo
    
    if [[ $placeholder_vars -gt 0 || $empty_vars -gt 0 ]]; then
        print_warning "Some variables have placeholder or empty values"
        print_warning "Container may not function correctly without proper configuration"
    fi
    
    return 0
}

# Function to build docker run environment arguments
build_env_args() {
    local env_file="$1"
    local env_args=""
    
    if [[ -z "$env_file" || ! -f "$env_file" ]]; then
        # No env file, just set PGHOST
        echo "-e PGHOST=${PGHOST}"
        return
    fi
    
    # Read environment file and build -e arguments
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip empty lines and comments
        if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        
        if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
            local key="${BASH_REMATCH[1]}"
            local value="${BASH_REMATCH[2]}"
            
            # Remove surrounding quotes if present
            value=$(echo "$value" | sed 's/^["'\'']\|["'\'']$//g')
            
            # Add to env args
            env_args="${env_args} -e ${key}=\"${value}\""
        fi
    done < "$env_file"
    
    # Override PGHOST for local container runtime
    env_args="${env_args} -e PGHOST=${PGHOST}"
    
    echo "$env_args"
}

# Remove existing containers if requested
if [ "$CLEAN_CONTAINERS" = true ]; then
  echo -e "\n${YELLOW}Checking for existing containers named '${CONTAINER_NAME}'...${NC}"
  if container_exists; then
    echo -e "${YELLOW}Removing existing container...${NC}"
    ${CONTAINER_CMD} rm -f ${CONTAINER_NAME}
    echo -e "${GREEN}✓ Container removed${NC}"
  else
    echo -e "${GREEN}✓ No containers to remove${NC}"
  fi
fi

# Print header
if [ "$BUILD_LOCAL" = true ]; then
  if [ "$USE_RANCHER" = true ]; then
    echo -e "${BLUE}Building FastAPI for Rancher Desktop with containerd (AMD64)${NC}"
  elif [ "$USE_PODMAN" = true ]; then
    echo -e "${BLUE}Building FastAPI for Local Mac Testing with Podman (AMD64)${NC}"
  else
    echo -e "${BLUE}Building FastAPI for Local Mac Testing (AMD64)${NC}"
  fi
else
  echo -e "${BLUE}Building FastAPI for Synology DS923+ (AMD64)${NC}"
fi

# Prepare build command
if [ "$USE_RANCHER" = true ]; then
  BUILD_OPTS="--platform=${PLATFORM}"
  if [ "$USE_CACHE" = false ]; then
      BUILD_OPTS="${BUILD_OPTS} --no-cache"
      echo -e "\n${YELLOW}Building without cache...${NC}"
  else
      echo -e "\n${YELLOW}Building with cache...${NC}"
  fi
elif [ "$USE_PODMAN" = true ]; then
  BUILD_OPTS="--platform=${PLATFORM}"
  if [ "$USE_CACHE" = false ]; then
      BUILD_OPTS="${BUILD_OPTS} --no-cache"
      echo -e "\n${YELLOW}Building without cache...${NC}"
  else
      echo -e "\n${YELLOW}Building with cache...${NC}"
  fi
else
  BUILD_OPTS="--platform=${PLATFORM} --load"
  if [ "$USE_CACHE" = false ]; then
      BUILD_OPTS="${BUILD_OPTS} --no-cache"
      echo -e "\n${YELLOW}Building without cache...${NC}"
  else
      echo -e "\n${YELLOW}Building with cache...${NC}"
  fi
fi

# Get to project root (script is now in scripts/ subdirectory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Build the image
if [ "$USE_RANCHER" = true ]; then
    echo -e "${YELLOW}Building with Rancher Desktop (nerdctl)...${NC}"
    nerdctl build ${BUILD_OPTS} -t ${IMAGE_NAME}:${IMAGE_TAG} .
elif [ "$USE_PODMAN" = true ]; then
    echo -e "${YELLOW}Building with Podman...${NC}"
    podman build ${BUILD_OPTS} -t ${IMAGE_NAME}:${IMAGE_TAG} .
else
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker buildx build ${BUILD_OPTS} -t ${IMAGE_NAME}:${IMAGE_TAG} .
fi

# Check if build was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful!${NC}"
    
    if [ "$BUILD_LOCAL" = false ]; then
        # Save the image for Synology
        echo -e "\n${YELLOW}Saving image to ${OUTPUT_FILE}...${NC}"
        ${CONTAINER_CMD} save ${IMAGE_NAME}:${IMAGE_TAG} > ${OUTPUT_FILE}
        
        if [ $? -eq 0 ]; then
            FILE_SIZE=$(du -h "${OUTPUT_FILE}" | cut -f1)
            echo -e "${GREEN}✓ Image saved (${FILE_SIZE})${NC}"
            
            echo -e "\n${YELLOW}Deployment Instructions:${NC}"
            echo -e "1. Transfer ${IMAGE_NAME}.tar to Synology NAS"
            echo -e "2. Container Manager → Registry → Import"
            echo -e "3. Create container and configure:"
            echo -e "   - Port: 9000:8080"
        else
            echo -e "${RED}✗ Failed to save image${NC}"
            exit 1
        fi
    elif [ "$RUN_CONTAINER" = true ]; then
        # Start a container with the built image
        print_header "Starting Container"
        
        # Load environment file if specified
        if load_env_file "$ENV_FILE"; then
            print_success "Environment loaded successfully"
        else
            print_warning "Using Dockerfile defaults"
        fi
        
        # Build environment arguments
        print_step "Preparing container environment..."
        ENV_ARGS=$(build_env_args "$ENV_FILE")
        
        # Show what we're about to run
        print_step "Container configuration:"
        echo -e "  Name: ${CONTAINER_NAME}"
        echo -e "  Port: ${PORT}"
        echo -e "  Image: ${IMAGE_NAME}:${IMAGE_TAG}"
        if [[ -n "$ENV_FILE" && -f "$ENV_FILE" ]]; then
            echo -e "  Env File: ${ENV_FILE}"
        else
            echo -e "  Env File: ${YELLOW}none (using defaults)${NC}"
        fi
        echo
        
        # Run the container (clean already removed any existing container)
        print_step "Creating and starting container..."
        
        # Use eval to properly handle the environment arguments
        eval "${CONTAINER_CMD} run -d --name ${CONTAINER_NAME} \
          -p ${PORT} \
          ${ENV_ARGS} \
          ${IMAGE_NAME}:${IMAGE_TAG}"
        
        if [ $? -eq 0 ]; then
            print_success "Container started successfully"
            
            if [ "$USE_RANCHER" = true ]; then
                echo -e "${GREEN}🌐 API available at http://localhost:9000 (via Rancher Desktop)${NC}"
            else
                echo -e "${GREEN}🌐 API available at http://localhost:9000${NC}"
            fi
            
            echo -e "${GREEN}📊 Health check: http://localhost:9000/health${NC}"
            echo
            
            print_step "Waiting for container to initialize..."
            sleep 3
            
            print_header "Container Logs"
            ${CONTAINER_CMD} logs ${CONTAINER_NAME}
            
            echo
            print_header "Container Status"
            
            # Show container status
            ${CONTAINER_CMD} ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
            
            echo
            print_step "Useful commands:"
            echo -e "  ${CYAN}View logs:${NC}      ${CONTAINER_CMD} logs -f ${CONTAINER_NAME}"
            echo -e "  ${CYAN}Stop container:${NC} ${CONTAINER_CMD} stop ${CONTAINER_NAME}"
            echo -e "  ${CYAN}Remove container:${NC} ${CONTAINER_CMD} rm -f ${CONTAINER_NAME}"
            echo -e "  ${CYAN}Check health:${NC}   curl http://localhost:9000/health"
            echo
        else
            print_error "Failed to start container"
            exit 1
        fi
    fi
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi 