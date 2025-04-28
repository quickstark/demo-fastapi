#!/bin/bash

# Parse command line arguments
USE_CACHE=true
BUILD_LOCAL=false
CLEAN_CONTAINERS=false
RUN_CONTAINER=false
CONTAINER_NAME="images"
PORT="9000:8080"
PGHOST="host.docker.internal"

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
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--no-cache] [--local] [--clean] [--run]"
      echo "  --no-cache    : Build without using Docker cache"
      echo "  --local       : Build for local testing instead of Synology"
      echo "  --clean       : Remove existing containers named '${CONTAINER_NAME}'"
      echo "  --run         : Start a container after build (implies --local, removes existing container)"
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

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if container exists
container_exists() {
  docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"
  return $?
}

# Function to check if container is running
container_running() {
  docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"
  return $?
}

# Remove existing containers if requested
if [ "$CLEAN_CONTAINERS" = true ]; then
  echo -e "\n${YELLOW}Checking for existing containers named '${CONTAINER_NAME}'...${NC}"
  if container_exists; then
    echo -e "${YELLOW}Removing existing container...${NC}"
    docker rm -f ${CONTAINER_NAME}
    echo -e "${GREEN}✓ Container removed${NC}"
  else
    echo -e "${GREEN}✓ No containers to remove${NC}"
  fi
fi

# Print header
if [ "$BUILD_LOCAL" = true ]; then
  echo -e "${BLUE}Building FastAPI for Local Mac Testing (AMD64)${NC}"
else
  echo -e "${BLUE}Building FastAPI for Synology DS923+ (AMD64)${NC}"
fi

# Prepare build command
BUILD_OPTS="--platform=${PLATFORM} --load"
if [ "$USE_CACHE" = false ]; then
    BUILD_OPTS="${BUILD_OPTS} --no-cache"
    echo -e "\n${YELLOW}Building without cache...${NC}"
else
    echo -e "\n${YELLOW}Building with cache...${NC}"
fi

# Build the image
echo -e "${YELLOW}Building Docker image...${NC}"
docker buildx build ${BUILD_OPTS} -t ${IMAGE_NAME}:${IMAGE_TAG} .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful!${NC}"
    
    if [ "$BUILD_LOCAL" = false ]; then
        # Save the image for Synology
        echo -e "\n${YELLOW}Saving image to ${OUTPUT_FILE}...${NC}"
        docker save ${IMAGE_NAME}:${IMAGE_TAG} > ${OUTPUT_FILE}
        
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
        docker run -d --name ${CONTAINER_NAME} \
          -p ${PORT} \
          -e PGHOST=${PGHOST} \
          ${IMAGE_NAME}:${IMAGE_TAG}
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Container started${NC}"
            echo -e "${GREEN}✓ API available at http://localhost:9000${NC}"
            echo -e "${YELLOW}Container logs:${NC}"
            sleep 2 # Give the container a moment to start up
            docker logs ${CONTAINER_NAME}
        else
            echo -e "${RED}✗ Failed to start container${NC}"
            exit 1
        fi
    fi
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi 