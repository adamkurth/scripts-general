#!/bin/bash

# Configuration variables
OLLAMA_PORT=11434
OPENWEBUI_PORT=3000
ICON_PATH="$HOME/Library/Safari/Icons"
DOCKER_COMPOSE_FILE="docker-compose.yml"

# Function to check if Docker Desktop is running
check_docker_desktop() {
    if ! pgrep -f "Docker Desktop" > /dev/null; then
        echo "Docker Desktop is not running. Please start Docker Desktop first."
        echo "You can start it from your Applications folder or menu bar."
        exit 1
    fi
    
    # Wait for Docker Desktop to be fully running
    echo "Checking Docker Desktop status..."
    until docker info > /dev/null 2>&1; do
        echo "Waiting for Docker Desktop to be ready..."
        sleep 2
    done
}

# Create Docker Compose configuration
create_docker_compose() {
    cat > $DOCKER_COMPOSE_FILE << EOL
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
}

# Create Safari web app icon
create_safari_icon() {
    mkdir -p "$ICON_PATH"
    
    cat > "$HOME/Desktop/OpenWebUI.webloc" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>URL</key>
    <string>http://localhost:${OPENWEBUI_PORT}</string>
    <key>IconURL</key>
    <string>https://raw.githubusercontent.com/open-webui/open-webui/main/public/logo.png</string>
</dict>
</plist>
EOL

    echo "Safari web app icon created on Desktop"
}

# Function to stop existing containers if they're running
cleanup_existing() {
    echo "Checking for existing containers..."
    if docker ps -q --filter "name=ollama" | grep -q .; then
        echo "Stopping existing Ollama container..."
        docker stop ollama
        docker rm ollama
    fi
    if docker ps -q --filter "name=openwebui" | grep -q .; then
        echo "Stopping existing OpenWebUI container..."
        docker stop openwebui
        docker rm openwebui
    fi
}

# Main execution
main() {
    echo "Starting Ollama with OpenWebUI setup using Docker Desktop..."
    
    # Check if Docker Desktop is running
    check_docker_desktop
    
    # Clean up existing containers
    cleanup_existing
    
    # Create Docker Compose configuration
    create_docker_compose
    echo "Docker Compose configuration created"
    
    # Start containers using Docker Compose
    echo "Starting containers with Docker Compose..."
    docker-compose up -d
    
    # Wait for services to be ready
    echo "Waiting for services to start..."
    echo "This might take a minute..."
    
    # Wait for Ollama to be ready
    until curl -s http://localhost:${OLLAMA_PORT}/api/version > /dev/null; do
        echo "Waiting for Ollama to be ready..."
        sleep 2
    done
    
    # Wait for OpenWebUI to be ready
    until curl -s http://localhost:${OPENWEBUI_PORT} > /dev/null; do
        echo "Waiting for OpenWebUI to be ready..."
        sleep 2
    done
    
    # Create Safari icon
    create_safari_icon
    
    echo ""
    echo "✅ Setup complete! Here's what was done:"
    echo "🐳 Docker containers are running"
    echo "🌐 OpenWebUI is available at http://localhost:${OPENWEBUI_PORT}"
    echo "🤖 Ollama API is available at http://localhost:${OLLAMA_PORT}"
    echo "🧭 Safari icon has been created on your Desktop"
    echo ""
    echo "To use:"
    echo "1. Double-click the OpenWebUI icon on your Desktop"
    echo "2. Select your preferred model in the OpenWebUI interface"
    echo "3. Start chatting!"
    echo ""
    echo "To stop the services:"
    echo "docker-compose down"
}

# Run the script
main