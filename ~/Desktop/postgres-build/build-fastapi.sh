#!/bin/bash

# Build script specifically for Synology DS923+ with AMD Ryzen R1600
# This script builds the FastAPI image for AMD64 architecture

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

# Print header
echo -e "${BLUE}=========================================================${NC}"
echo -e "${BLUE}   FastAPI Builder for Synology DS923+                   ${NC}"
echo -e "${BLUE}   (AMD Ryzen R1600 - AMD64 Architecture)                ${NC}"
echo -e "${BLUE}=========================================================${NC}"

# Create a temporary Dockerfile for the FastAPI app if not in current directory
if [ ! -f "Dockerfile.fastapi" ]; then
    echo -e "\n${YELLOW}Creating FastAPI Dockerfile...${NC}"
    cat > Dockerfile.fastapi << EOF
FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables with updated agent name
ENV PYTHONPATH=/app \\
    PORT=8080 \\
    DD_ENV="dev" \\
    DD_SERVICE="fastapi-app" \\
    DD_VERSION="1.0" \\
    DD_LOGS_INJECTION=true \\
    DD_TRACE_SAMPLE_RATE=1 \\
    DD_PROFILING_ENABLED=true \\
    DD_DYNAMIC_INSTRUMENTATION_ENABLED=true \\
    DD_SYMBOL_DATABASE_UPLOAD_ENABLED=true

# Use python -m to run hypercorn
CMD ["python", "-m", "hypercorn", "main:app", "--bind", "0.0.0.0:8080"]

EXPOSE 8080
EOF
    echo -e "${GREEN}✓ FastAPI Dockerfile created${NC}"
fi

# Build the Docker image with platform specification
echo -e "\n${YELLOW}Building FastAPI image for AMD64 architecture...${NC}"
docker build --platform=${PLATFORM} -t ${IMAGE_NAME}:${IMAGE_TAG} -f Dockerfile.fastapi .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful!${NC}"
    
    # Save the image to Desktop
    echo -e "\n${YELLOW}Saving image to Desktop...${NC}"
    echo -e "Saving to: ${OUTPUT_FILE}"
    
    # Create progress animation
    echo -n "Saving image "
    docker save ${IMAGE_NAME}:${IMAGE_TAG} > ${OUTPUT_FILE} &
    pid=$!
    
    # Show a spinner while saving
    spin='-\|/'
    i=0
    while kill -0 $pid 2>/dev/null
    do
        i=$(( (i+1) % 4 ))
        printf "\r[%c] Saving image... " "${spin:$i:1}"
        sleep .1
    done
    
    # Check if save was successful
    wait $pid
    if [ $? -eq 0 ]; then
        printf "\r${GREEN}✓ Image saved successfully!${NC}                 \n"
        
        # Create compressed version
        echo -e "\n${YELLOW}Creating compressed version...${NC}"
        gzip -c ${OUTPUT_FILE} > ${OUTPUT_FILE}.gz
        
        # Get file sizes
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            FILE_SIZE=$(du -h "${OUTPUT_FILE}" | cut -f1)
            GZ_FILE_SIZE=$(du -h "${OUTPUT_FILE}.gz" | cut -f1)
        else
            # Linux
            FILE_SIZE=$(du -h "${OUTPUT_FILE}" | cut -f1)
            GZ_FILE_SIZE=$(du -h "${OUTPUT_FILE}.gz" | cut -f1)
        fi
        
        echo -e "\n${GREEN}Summary:${NC}"
        echo -e "  Image name: ${IMAGE_NAME}:${IMAGE_TAG}"
        echo -e "  Architecture: ${PLATFORM} (for AMD Ryzen R1600)"
        echo -e "  Saved to: ${OUTPUT_FILE}"
        echo -e "  File size: ${FILE_SIZE}"
        echo -e "  Compressed: ${OUTPUT_FILE}.gz"
        echo -e "  Compressed size: ${GZ_FILE_SIZE}"
        
        echo -e "\n${YELLOW}DS923+ Deployment Instructions:${NC}"
        echo -e "1. Transfer ${IMAGE_NAME}.tar or ${IMAGE_NAME}.tar.gz to your Synology NAS"
        echo -e "2. In Container Manager, go to \"Registry\" → \"Import\" and select the file"
        echo -e "3. Create a new container from this image"
        echo -e "4. Configure the following:"
        echo -e "   a. Set port mapping: 8080:8080"
        echo -e "   b. Configure environment variables from .env file"
        echo -e "   c. Ensure PostgreSQL container is running and accessible"
        echo -e "   d. Update PGHOST in environment variables to the internal container network address"
    else
        echo -e "\n${RED}✗ Failed to save image to Desktop.${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Build failed.${NC}"
    exit 1
fi 