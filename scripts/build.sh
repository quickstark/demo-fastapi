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
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--no-cache] [--local] [--clean] [--run] [--podman] [--rancher]"
      echo "  --no-cache    : Build without using Docker cache"
      echo "  --local       : Build for local testing instead of Synology"
      echo "  --clean       : Remove existing containers named '${CONTAINER_NAME}'"
      echo "  --run         : Start a container after build (implies --local, removes existing container)"
      echo "  --podman      : Build for Podman instead of Docker"
      echo "  --rancher     : Build for Rancher Desktop with containerd/nerdctl"
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
NC='\033[0m' # No Color

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
        echo -e "\n${YELLOW}Starting container...${NC}"
        
        # Run the container (clean already removed any existing container)
        echo -e "${YELLOW}Creating and starting container...${NC}"
        ${CONTAINER_CMD} run -d --name ${CONTAINER_NAME} \
          -p ${PORT} \
          -e PGHOST=${PGHOST} \
          ${IMAGE_NAME}:${IMAGE_TAG}
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Container started${NC}"
            if [ "$USE_RANCHER" = true ]; then
                echo -e "${GREEN}✓ API available at http://localhost:9000 (via Rancher Desktop)${NC}"
            else
                echo -e "${GREEN}✓ API available at http://localhost:9000${NC}"
            fi
            echo -e "${YELLOW}Container logs:${NC}"
            sleep 2 # Give the container a moment to start up
            ${CONTAINER_CMD} logs ${CONTAINER_NAME}
        else
            echo -e "${RED}✗ Failed to start container${NC}"
            exit 1
        fi
    fi
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi 