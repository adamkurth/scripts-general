#!/bin/bash

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration variables
OLLAMA_PORT=11434
OPENWEBUI_PORT=3000
LAUNCHER_SCRIPT="$HOME/ollama-launcher.sh"
BOOKMARK_NAME="Ollama WebUI"

# Print styled messages
print_info() {
    echo -e "${BLUE}ℹ️  ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✅ ${NC}$1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  ${NC}$1"
}

print_error() {
    echo -e "${RED}❌ ${NC}$1"
}

print_header() {
    echo -e "\n${PURPLE}${BOLD}$1${NC}\n"
}

# Function to check if Docker Desktop is running
check_docker_desktop() {
    print_header "Checking Docker Desktop Status"
    if ! pgrep -f "Docker Desktop" > /dev/null; then
        print_error "Docker Desktop is not running. Please start Docker Desktop first."
        print_info "You can start it from your Applications folder or menu bar."
        exit 1
    fi
    
    print_info "Checking Docker Desktop connection..."
    until docker info > /dev/null 2>&1; do
        echo -e "${YELLOW}⏳ Waiting for Docker Desktop to be ready...${NC}"
        sleep 2
    done
    print_success "Docker Desktop is running and ready"
}

# Create launcher script
create_launcher_script() {
    cat > "$LAUNCHER_SCRIPT" << EOL
#!/bin/bash

# Start Docker containers if they're not running
if ! docker ps | grep -q ollama; then
    docker-compose -f $HOME/docker-compose.yml up -d
    echo "Starting Ollama services..."
    sleep 5
fi

# Open Safari and navigate to OpenWebUI in a new tab
osascript <<EOL
tell application "Safari"
    activate
    tell window 1
        set current_tab to current tab
        make new tab with properties {URL:"http://localhost:${OPENWEBUI_PORT}"}
        set current tab to current_tab
    end tell
end tell
EOL
EOL

    chmod +x "$LAUNCHER_SCRIPT"
    print_success "Created launcher script at: $LAUNCHER_SCRIPT"
}

# Create Docker Compose configuration
create_docker_compose() {
    print_header "Creating Docker Configuration"
    cat > "$HOME/docker-compose.yml" << EOL
version: '3.8'
services:
  ollama:
    container_name: ollama
    image: ollama/ollama:latest
    ports:
      - "${OLLAMA_PORT}:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    networks:
      - ollama-network

  openwebui:
    container_name: openwebui
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "${OPENWEBUI_PORT}:8080"
    environment:
      - OLLAMA_API_BASE_URL=http://ollama:11434/api
    depends_on:
      - ollama
    restart: unless-stopped
    networks:
      - ollama-network

networks:
  ollama-network:
    name: ollama-network

volumes:
  ollama_data:
    name: ollama_data
EOL
    print_success "Docker Compose configuration created"
}

# Create Safari integration
create_safari_integration() {
    print_header "Creating Safari Integration"
    
    # Create Desktop shortcut that runs the launcher
    cat > "$HOME/Desktop/Ollama-WebUI.command" << EOL
#!/bin/bash
"$LAUNCHER_SCRIPT"
EOL
    chmod +x "$HOME/Desktop/Ollama-WebUI.command"
    
    # Add to Safari favorites and open in new tab using applescript
    osascript <<EOL
tell application "Safari"
    # Add bookmark
    set newBookmark to make new bookmark item at end of bookmarks menu with properties {name:"$BOOKMARK_NAME", url:"http://localhost:${OPENWEBUI_PORT}"}
    
    # Open in new tab
    activate
    tell window 1
        make new tab with properties {URL:"http://localhost:${OPENWEBUI_PORT}"}
    end tell
end tell
EOL

    print_success "Safari integration created"
    print_info "Added launcher script at: $LAUNCHER_SCRIPT"
    print_info "Created Desktop icon: Ollama-WebUI"
    print_info "Added Safari bookmark: $BOOKMARK_NAME"
}

# Function to stop existing containers if they're running
cleanup_existing() {
    print_header "Checking Existing Containers"
    if docker ps -q --filter "name=ollama" | grep -q .; then
        print_warning "Stopping existing Ollama container..."
        docker stop ollama
        docker rm ollama
    fi
    if docker ps -q --filter "name=openwebui" | grep -q .; then
        print_warning "Stopping existing OpenWebUI container..."
        docker stop openwebui
        docker rm openwebui
    fi
    print_success "Cleanup complete"
}

# Main execution
main() {
    print_header "🚀 Starting Ollama with OpenWebUI Setup"
    
    # Check if Docker Desktop is running
    check_docker_desktop
    
    # Clean up existing containers
    cleanup_existing
    
    # Create Docker Compose configuration
    create_docker_compose
    
    # Start containers using Docker Compose
    print_header "Starting Containers"
    docker-compose -f "$HOME/docker-compose.yml" up -d
    
    # Wait for services to be ready
    print_info "Waiting for services to start..."
    
    # Wait for Ollama to be ready
    until curl -s http://localhost:${OLLAMA_PORT}/api/version > /dev/null; do
        echo -e "${YELLOW}⏳ Waiting for Ollama to be ready...${NC}"
        sleep 2
    done
    
    # Wait for OpenWebUI to be ready
    until curl -s http://localhost:${OPENWEBUI_PORT} > /dev/null; do
        echo -e "${YELLOW}⏳ Waiting for OpenWebUI to be ready...${NC}"
        sleep 2
    done
    
    # Create launcher script and Safari integration
    create_launcher_script
    create_safari_integration
    
    print_header "🎉 Setup Complete!"
    echo -e "${GREEN}✨ Here's what was done:${NC}"
    echo -e "${CYAN}🐳 Docker containers are running"
    echo -e "🌐 OpenWebUI is available at http://localhost:${OPENWEBUI_PORT}"
    echo -e "🤖 Ollama API is available at http://localhost:${OLLAMA_PORT}"
    echo -e "🧭 Safari bookmark and Desktop launcher created${NC}"
    echo ""
    echo -e "${YELLOW}To use:${NC}"
    echo "1. Click the Ollama-WebUI icon on your Desktop"
    echo "2. Or use the Safari bookmark"
    echo "3. Select your preferred model in the OpenWebUI interface"
    echo ""
    echo -e "${YELLOW}To stop the services:${NC}"
    echo "docker-compose down"
}

# Run the script
main