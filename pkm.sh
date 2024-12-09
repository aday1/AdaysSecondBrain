#!/bin/bash

# Color definitions
RED='\033[0;31m'
NC='\033[0m' # No Color

# Emoji definitions
EMOJI_ERROR="❌"
EMOJI_SUCCESS="✅"
EMOJI_BACKUP="💾"
EMOJI_RESTORE="🔄"
EMOJI_CONFIG="⚙️"
EMOJI_WEB="🌐"
EMOJI_DB="🗄️"
EMOJI_DAILY="📅"
EMOJI_HELP="❓"

# Check for gum installation
check_gum() {
    if ! command -v gum &> /dev/null; then
        echo "Installing gum for modern terminal UI..."
        if command -v brew &> /dev/null; then
            brew install gum
        elif command -v apt-get &> /dev/null; then
            sudo mkdir -p /etc/apt/keyrings
            curl -fsSL https://repo.charm.sh/apt/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/charm.gpg
            echo "deb [signed-by=/etc/apt/keyrings/charm.gpg] https://repo.charm.sh/apt/ * *" | sudo tee /etc/apt/sources.list.d/charm.list
            sudo apt update && sudo apt install gum
        else
            echo "Please install gum manually: https://github.com/charmbracelet/gum#installation"
            exit 1
        fi
    fi
}

# Function to display styled error
display_error() {
    local error_msg="$1"
    echo -e "${RED}${EMOJI_ERROR} $error_msg${NC}"
}

# Function to display styled success
display_success() {
    local msg="$1"
    echo -e "\033[0;32m${EMOJI_SUCCESS} $msg\033[0m"
}

# Function to wait for user input
wait_for_key() {
    read -p "Press Enter to continue..."
}

# Ensure bcrypt is installed
ensure_bcrypt() {
    if ! python3 -c "import bcrypt" &> /dev/null; then
        echo "Installing bcrypt..."
        pip install bcrypt
    fi
}

# Check if virtual environment exists
if [ ! -d "pkm_venv" ]; then
    display_error "Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Activate virtual environment
VENV_ACTIVATE="pkm_venv/bin/activate"
if [ ! -f "$VENV_ACTIVATE" ]; then
    display_error "Virtual environment activation script not found. Please run install.sh first."
    exit 1
fi

source "$VENV_ACTIVATE"

# Ensure bcrypt is installed
ensure_bcrypt

# Database paths
DB_PATH="pkm/db/pkm.db"
INIT_SQL="db/init.sql"
BACKUP_DIR="pkm/db/backups"
LAST_BACKUP_FILE="pkm/db/.last_backup"

# MD files paths
DAILY_DIR="daily"
MD_BACKUP_DIR="pkm/db/md_backups"

# Function to show help
show_help() {
    echo "
    $EMOJI_HELP PKM System Launcher

    Usage: ./pkm.sh [option]

    Options:
    $EMOJI_WEB web           Start the web interface
    $EMOJI_CONFIG config        Open the configuration menu
    $EMOJI_DB init-db       Initialize the database
    $EMOJI_BACKUP backup-db     Create a database backup
    $EMOJI_RESTORE restore-db    Restore database from backup
    $EMOJI_BACKUP backup-md     Create a backup of markdown files
    $EMOJI_RESTORE restore-md    Restore markdown files from backup
    $EMOJI_HELP help          Show this help message
    $EMOJI_CONFIG change-password  Change a user's password

    No option will start the menu interface"
}

# Function to backup markdown files
backup_md() {
    mkdir -p "$MD_BACKUP_DIR"
    TIMESTAMP=$(get_formatted_timestamp)
    BACKUP_PATH="$MD_BACKUP_DIR/md_${TIMESTAMP}.tar.gz"
    
    if [ -d "$DAILY_DIR" ]; then
        tar -czf "$BACKUP_PATH" "$DAILY_DIR"
        if [ $? -eq 0 ]; then
            display_success "Markdown files backed up to: $BACKUP_PATH"
            if [ "$1" != "silent" ]; then
                wait_for_key
            fi
        else
            display_error "Error creating markdown backup."
            wait_for_key
            exit 1
        fi
    else
        display_error "Daily directory not found."
        wait_for_key
        exit 1
    fi
}

# Function to restore markdown files
restore_md() {
    if [ ! -d "$MD_BACKUP_DIR" ]; then
        display_error "No markdown backups directory found."
        wait_for_key
        exit 1
    fi

    # List available backups with most recent first
    echo "Available markdown backups (most recent first):"
    BACKUPS=($(ls -1t "$MD_BACKUP_DIR"))
    SELECTED=$(gum choose "Cancel restore" "${BACKUPS[@]}")
    
    if [ "$SELECTED" = "Cancel restore" ]; then
        echo "Markdown restore cancelled."
        wait_for_key
        return
    fi
    
    # Confirm restore
    if gum confirm "Are you sure you want to restore markdown files from $SELECTED?"; then
        # Create a backup of current markdown files before restore
        echo "Creating backup of current markdown files before restore..."
        backup_md "silent"
        
        # Remove existing daily directory and restore from backup
        rm -rf "$DAILY_DIR"
        gum spin --spinner dot --title "Restoring from backup..." -- tar -xzf "$MD_BACKUP_DIR/$SELECTED"
        
        if [ $? -eq 0 ]; then
            display_success "Markdown files restored successfully from: $SELECTED"
            wait_for_key
        else
            display_error "Error restoring markdown files."
            wait_for_key
            exit 1
        fi
    else
        echo "Markdown restore cancelled."
        wait_for_key
    fi
}

# Function to initialize database
init_db() {
    echo "Database Initialization Information:"
    echo "--------------------------------"
    echo "This will create or reinitialize the following tables:"
    echo "1. habits - Habit tracking definitions"
    echo "2. habit_logs - Daily habit completion records"
    echo "3. alcohol_logs - Alcohol consumption tracking"
    echo "4. work_logs - Work hours and project tracking"
    echo "5. daily_metrics - Daily mood, energy, and sleep tracking"
    echo "6. goals - Goal tracking and planning"

    if [ -f "$DB_PATH" ]; then
        read -p "Database already exists. Do you want to reinitialize it? (y/n): " REINIT
        if [[ "$REINIT" != "y" ]]; then
            echo "Database initialization cancelled."
            return
        fi
        echo "Backing up existing database before reinitialization..."
        backup_db "silent"
        echo "Removing existing database..."
        rm "$DB_PATH"
    fi

    # Ask about markdown files
    if [ -d "$DAILY_DIR" ] && [ "$(ls -A $DAILY_DIR)" ]; then
        read -p "Do you want to backup and remove existing markdown files as well? (y/n): " BACKUP_MD
        if [[ "$BACKUP_MD" == "y" ]]; then
            echo "Backing up markdown files before removal..."
            backup_md "silent"
            echo "Removing markdown files..."
            rm -rf "$DAILY_DIR"
            mkdir -p "$DAILY_DIR"
        fi
    fi
    
    echo "Initializing database..."
    sqlite3 "$DB_PATH" < "$INIT_SQL"
    if [ $? -eq 0 ]; then
        # Apply update schema
        sqlite3 "$DB_PATH" < "pkm/web/update_schema.sql"
        if [ $? -eq 0 ]; then
            echo "Database initialized successfully with empty tables."
            echo "You can now track:"
            echo "- Habits and their completion"
            echo "- Alcohol consumption"
            echo "- Work hours and projects"
            echo "- Daily metrics (mood, energy, sleep)"
            echo "- Goals and plans"
        else
            echo "Error applying schema updates."
            exit 1
        fi
    else
        echo "Error initializing database."
        exit 1
    fi
}

# Function to get formatted timestamp
get_formatted_timestamp() {
    date "+pkmdb_%B_%d_%Y_%I%M%p"
}

# Function to get machine readable timestamp
get_machine_timestamp() {
    date "+%Y%m%d"
}

# Function to backup database
backup_db() {
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(get_formatted_timestamp)
    BACKUP_PATH="$BACKUP_DIR/${TIMESTAMP}.db"
    
    if [ -f "$DB_PATH" ]; then
        cp "$DB_PATH" "$BACKUP_PATH"
        if [ $? -eq 0 ]; then
            display_success "Database backed up to: $BACKUP_PATH"
            get_machine_timestamp > "$LAST_BACKUP_FILE"
            if [ "$1" != "silent" ]; then
                wait_for_key
            fi
        else
            display_error "Error creating backup."
            wait_for_key
            exit 1
        fi
    else
        display_error "Database file not found."
        wait_for_key
        exit 1
    fi
}

# Function to restore database
restore_db() {
    if [ ! -d "$BACKUP_DIR" ]; then
        display_error "No backups directory found."
        wait_for_key
        exit 1
    fi

    # List available backups with most recent first
    echo "Available backups (most recent first):"
    BACKUPS=($(ls -1t "$BACKUP_DIR"))
    SELECTED=$(gum choose "Cancel restore" "${BACKUPS[@]}")
    
    if [ "$SELECTED" = "Cancel restore" ]; then
        echo "Database restore cancelled."
        wait_for_key
        return
    fi
    
    if gum confirm "Are you sure you want to restore from $SELECTED?"; then
        # Create a backup of current database before restore
        echo "Creating backup of current database before restore..."
        backup_db "silent"
        
        # Restore the selected backup
        cp "$BACKUP_DIR/$SELECTED" "$DB_PATH"
        if [ $? -eq 0 ]; then
            display_success "Database restored successfully from: $SELECTED"
            wait_for_key
        else
            display_error "Error restoring database."
            wait_for_key
            exit 1
        fi
    else
        echo "Database restore cancelled."
        wait_for_key
    fi
}

# Function to check daily backup
check_daily_backup() {
    mkdir -p "$BACKUP_DIR"
    
    if [ ! -f "$LAST_BACKUP_FILE" ]; then
        echo "No previous backup found. Creating initial backup..."
        backup_db "silent"
        return
    fi
    
    LAST_BACKUP_DATE=$(cat "$LAST_BACKUP_FILE")
    TODAY=$(get_machine_timestamp)
    
    if [[ "$LAST_BACKUP_DATE" != "$TODAY" ]]; then
        echo "Creating daily backup..."
        backup_db "silent"
    fi
}

# Function to check if web interface is enabled and get port
check_web_config() {
    if [ ! -f "pkm/web/config.json" ]; then
        display_error "Web configuration file not found."
        return 1
    fi
    
    # Check if web is enabled
    if ! grep -q '"web_enabled": true' "pkm/web/config.json"; then
        display_error "Web interface is not enabled in config. Please enable it in pkm/web/config.json first."
        return 1
    fi
    
    # Extract port number from config
    PORT=$(grep -o '"port": [0-9]*' "pkm/web/config.json" | grep -o '[0-9]*')
    if [ -z "$PORT" ]; then
        display_error "Could not determine port from config."
        return 1
    fi
    
    echo "$PORT"
    return 0
}

# Function to check and handle existing Flask processes
check_flask_processes() {
    # Get configured port
    PORT=$(check_web_config)
    if [ $? -ne 0 ]; then
        exit 1
    fi
    
    # Check if port is in use
    if netstat -tuln | grep -q ":$PORT "; then
        # Get PIDs of processes using the port
        port_pids=$(lsof -t -i:$PORT)
        if [ ! -z "$port_pids" ]; then
            echo "Found processes using port $PORT:"
            for pid in $port_pids; do
                # Check if this PID belongs to a PKM process
                if ps -p $pid -o cmd= | grep -q "python3 -m pkm.web.app"; then
                    if gum confirm "PKM web server already running (PID: $pid). Would you like to stop it and start a new instance?"; then
                        echo "Stopping PKM web server..."
                        kill $pid
                        sleep 1
                        # Force kill if still running
                        if ps -p $pid > /dev/null; then
                            kill -9 $pid
                        fi
                        return 0
                    else
                        echo "Keeping existing PKM web server running."
                        exit 0
                    fi
                fi
            done
            display_error "Port $PORT is in use by non-PKM process(es). Please either free up port $PORT or change the port in web config."
            exit 1
        fi
    fi
    
    # Check for any other Flask processes that might not be bound to port yet
    existing_pids=$(pgrep -f "python3 -m pkm.web.app")
    if [ ! -z "$existing_pids" ]; then
        echo "Found existing Flask processes:"
        ps -p $existing_pids -o pid,cmd
        if gum confirm "Would you like to kill these processes?"; then
            echo "Killing existing processes..."
            kill $existing_pids
            sleep 1
            # Double check if any processes are still hanging
            if pgrep -f "python3 -m pkm.web.app" > /dev/null; then
                echo "Force killing remaining processes..."
                pkill -9 -f "python3 -m pkm.web.app"
            fi
            echo "All existing processes have been terminated."
        else
            echo "Keeping existing processes running."
            echo "Warning: Starting a new instance might cause port conflicts."
        fi
    fi
}

# Function to change password
change_password() {
    CONFIG_PATH="pkm/web/config.json"
    if [ ! -f "$CONFIG_PATH" ]; then
        display_error "config.json not found."
        exit 1
    fi

    # Load the current config
    CONFIG=$(python3 -c "
import json
config_path = '$CONFIG_PATH'
with open(config_path, 'r') as f:
    config = json.load(f)
print(json.dumps(config))
")
    if [ $? -ne 0 ]; then
        display_error "Failed to load config.json."
        exit 1
    fi

    # Extract the current username
    USERNAME=$(echo "$CONFIG" | python3 -c "import sys, json; print(json.load(sys.stdin)['username'])")

    read -sp "Enter new password for $USERNAME: " USER_PASSWORD
    echo
    read -sp "Confirm new password for $USERNAME: " CONFIRM_PASSWORD
    echo
    if [ "$USER_PASSWORD" != "$CONFIRM_PASSWORD" ]; then
        display_error "Passwords do not match."
        exit 1
    fi

    # Update password_hash in config.json using werkzeug.security.generate_password_hash
    echo "Updating password_hash for user $USERNAME in config.json"
    python3 -c "
import json
from werkzeug.security import generate_password_hash

config_path = '$CONFIG_PATH'
username = '$USERNAME'
password = '$USER_PASSWORD'

with open(config_path, 'r') as f:
    config = json.load(f)

config['password_hash'] = generate_password_hash(password)

with open(config_path, 'w') as f:
    json.dump(config, f, indent=4)
"
    if [ $? -eq 0 ]; then
        display_success "Password_hash for user $USERNAME updated successfully in config.json."
    else
        display_error "Failed to update password_hash for user $USERNAME in config.json."
        exit 1
    fi
}

# Function to show tables in the database
show_tables() {
    echo "Tables in the database:"
    sqlite3 "$DB_PATH" ".tables"
}

# Install gum if not present
check_gum

# Check for daily backup before processing any command
check_daily_backup

# Check command line arguments
case "$1" in
    "web")
        PORT=$(check_web_config)
        if [ $? -ne 0 ]; then
            exit 1
        fi
        echo "Checking for existing web instances..."
        check_flask_processes
        echo "Starting web interface on port $PORT..."
        python3 -m pkm.web.app  # Removed SQL execution logic
        ;;
    "config")
        echo "$EMOJI_CONFIG Opening configuration menu..."
        python3 -m pkm.config_menu
        ;;
    "init-db")
        init_db
        ;;
    "backup-db")
        backup_db
        ;;
    "restore-db")
        restore_db
        ;;
    "backup-md")
        backup_md
        ;;
    "restore-md")
        restore_md
        ;;
    "change-password")
        change_password
        ;;
    "show-tables")
        show_tables
        ;;
    "help")
        show_help
        ;;
    "")
        # Run menu interface (replacing theme selection)
        python3 -m pkm.menu_ui
        ;;
    *)
        display_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac

# Only try to deactivate if we're in a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi
