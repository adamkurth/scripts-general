#!/bin/bash

# run_ollama.sh - Script to start an interactive session and run Ollama
# Usage: ./run_ollama.sh [model_name] [hours]

# Default values
DEFAULT_MODEL="mistral"
DEFAULT_HOURS=4

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get arguments
MODEL=${1:-$DEFAULT_MODEL}
HOURS=${2:-$DEFAULT_HOURS}

# Print banner
echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}  Ollama Runner for SOL Supercomputer${NC}"
echo -e "${GREEN}=========================================${NC}\n"

# Check if we're on a login node
if [[ ! "$(hostname)" =~ "login" ]]; then
    echo -e "${YELLOW}[!]${NC} Already on a compute node. Running setup directly..."
    ./setup_ollama.sh "$MODEL"
    exit 0
fi

# Create a temporary script to run after getting the interactive session
TMP_SCRIPT=$(mktemp)
cat > "$TMP_SCRIPT" << EOF
#!/bin/bash
cd "\$(pwd)"
./setup_ollama.sh "$MODEL"
EOF
chmod +x "$TMP_SCRIPT"

echo -e "${GREEN}[+]${NC} Requesting interactive session for ${HOURS} hours..."
echo -e "${GREEN}[+]${NC} Will run ${MODEL} model after session starts..."

# Start interactive session
interactive -G 1 -t 0-${HOURS}:00 "$TMP_SCRIPT"

# Clean up
rm "$TMP_SCRIPT"