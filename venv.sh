#!/bin/bash

# Color definitions
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display status
display_status() {
    local msg="$1"
    echo -e "${BLUE}ℹ️ $msg${NC}"
}

# Function to display success
display_success() {
    local msg="$1"
    echo -e "${GREEN}✅ $msg${NC}"
}

# Function to display error
display_error() {
    local msg="$1"
    echo -e "${RED}❌ $msg${NC}"
}

# Function to display help
show_help() {
    echo -e "${BLUE}PKM Shell Scripts Overview:${NC}"
    echo
    echo "Available shell scripts in this project:"
    echo
    echo -e "${GREEN}1. venv.sh${NC} (this script)"
    echo "   Purpose: Manages the Python virtual environment"
    echo "   Commands:"
    echo "   - source venv.sh activate   : Activates the virtual environment"
    echo "   - source venv.sh deactivate : Deactivates the virtual environment"
    echo
    echo -e "${GREEN}2. install.sh${NC}"
    echo "   Purpose: Main installation script"
    echo "   - Checks Python installation"
    echo "   - Creates virtual environment"
    echo "   - Installs requirements"
    echo "   - Initializes databases"
    echo "   - Sets up directory structure"
    echo
    echo -e "${GREEN}3. setup.sh${NC}"
    echo "   Purpose: Basic setup script"
    echo "   - Creates virtual environment"
    echo "   - Installs requirements"
    echo "   - Simpler alternative to install.sh"
    echo
    echo -e "${GREEN}4. pkm.sh${NC}"
    echo "   Purpose: Main application launcher"
    echo "   Commands:"
    echo "   - ./pkm.sh web        : Start web interface"
    echo "   - ./pkm.sh config     : Open configuration menu"
    echo "   - ./pkm.sh init-db    : Initialize database"
    echo "   - ./pkm.sh backup-db  : Create database backup"
    echo "   - ./pkm.sh restore-db : Restore database"
    echo "   - ./pkm.sh backup-md  : Backup markdown files"
    echo "   - ./pkm.sh restore-md : Restore markdown files"
    echo
    echo -e "${GREEN}5. demo.sh${NC}"
    echo "   Purpose: Demo data management"
    echo "   - Generates sample data for testing"
    echo "   - Creates backups before generating demo data"
    echo "   - Allows specifying months of demo data"
    echo
    echo -e "${GREEN}6. cleanup.sh${NC}"
    echo "   Purpose: System cleanup"
    echo "   - Removes Python bytecode files"
    echo "   - Cleans virtual environment"
    echo "   - Manages database backups"
    echo "   - Cleans daily markdown files"
    echo
}

VENV_PATH="pkm_venv"
VENV_ACTIVATE="$VENV_PATH/bin/activate"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    display_error "Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Check if activation script exists
if [ ! -f "$VENV_ACTIVATE" ]; then
    display_error "Virtual environment activation script not found. Please run install.sh first."
    exit 1
fi

# Function to activate virtual environment
activate_venv() {
    if [ -n "$VIRTUAL_ENV" ]; then
        if [[ "$VIRTUAL_ENV" == *"$VENV_PATH"* ]]; then
            display_status "Virtual environment is already activated"
            return 0
        else
            display_status "Deactivating current virtual environment..."
            deactivate 2>/dev/null
        fi
    fi
    
    display_status "Activating virtual environment..."
    source "$VENV_ACTIVATE"
    
    # Debug statement to confirm activation
    if [ -n "$VIRTUAL_ENV" ]; then
        display_success "Virtual environment activated: $VIRTUAL_ENV"
    else
        display_error "Failed to activate virtual environment"
        return 1
    fi
}

# Function to deactivate virtual environment
deactivate_venv() {
    if [ -z "$VIRTUAL_ENV" ]; then
        display_status "No virtual environment is currently activated"
        return 0
    fi
    
    if [[ "$VIRTUAL_ENV" == *"$VENV_PATH"* ]]; then
        display_status "Deactivating virtual environment..."
        deactivate
        display_success "Virtual environment deactivated"
    else
        display_error "Different virtual environment is active. Please deactivate it manually."
    fi
}

# Process command line arguments
case "$1" in
    "activate")
        activate_venv
        ;;
    "deactivate")
        deactivate_venv
        ;;
    "help")
        show_help
        ;;
    *)
        echo "Usage: source venv.sh [activate|deactivate|help]"
        echo "  activate   - Activate the PKM virtual environment"
        echo "  deactivate - Deactivate the PKM virtual environment"
        echo "  help       - Show help about all shell scripts"
        ;;
esac
