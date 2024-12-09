#!/bin/bash

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in a virtual environment and deactivate if we are
if [ -n "$VIRTUAL_ENV" ] && type deactivate >/dev/null 2>&1; then
    echo -e "${BLUE}🔄 Deactivating existing virtual environment...${NC}"
    deactivate
fi

echo -e "${BLUE}🔍 Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3 to continue.${NC}"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.6"

# Version comparison function
version_compare() {
    echo "$1 $2" | awk '{
        split($1, a, ".");
        split($2, b, ".");
        for (i = 1; i <= length(a) && i <= length(b); i++) {
            if (a[i] < b[i]) exit 1;
            if (a[i] > b[i]) exit 0;
        }
        if (length(a) < length(b)) exit 1;
        exit 0;
    }'
}

if ! version_compare "$python_version" "$required_version"; then
    echo -e "${RED}❌ Python version must be 3.6 or higher. Current version: $python_version${NC}"
    exit 1
fi

echo -e "${BLUE}🔍 Checking for venv module...${NC}"
python3 -c "import venv" 2>/dev/null || {
    echo -e "${RED}❌ Python venv module is not installed. Please install python3-venv package.${NC}"
    exit 1
}

# Create virtual environment if it doesn't exist
if [ ! -d "pkm_venv" ]; then
    echo -e "${BLUE}🔧 Creating virtual environment...${NC}"
    python3 -m venv pkm_venv
fi

# Activate virtual environment
echo -e "${BLUE}🚀 Activating virtual environment...${NC}"
source pkm_venv/bin/activate

# Install requirements
echo -e "${BLUE}📦 Installing requirements...${NC}"
pip install -r requirements.txt

# Initialize databases
echo -e "${YELLOW}💾 Initializing databases...${NC}"

# Main database in db/
echo -e "${BLUE}🗄️  Setting up main database...${NC}"
mkdir -p db
mkdir -p db/backups
touch db/backups/.gitignore
if [ ! -f "db/pkm.db" ]; then
    echo -e "${YELLOW}📝 Creating db/pkm.db...${NC}"
    sqlite3 db/pkm.db < db/init.sql
    sqlite3 db/pkm.db < pkm/web/update_schema.sql
fi

# PKM database in pkm/db/
echo -e "${BLUE}🗄️  Setting up PKM database...${NC}"
mkdir -p pkm/db
mkdir -p pkm/db/backups
mkdir -p pkm/db/md_backups
touch pkm/db/backups/.gitignore
if [ ! -f "pkm/db/pkm.db" ]; then
    echo -e "${YELLOW}📝 Creating pkm/db/pkm.db...${NC}"
    sqlite3 pkm/db/pkm.db < db/init.sql
    sqlite3 pkm/db/pkm.db < pkm/web/update_schema.sql
fi

# Create daily directories if they don't exist
echo -e "${BLUE}📁 Setting up daily log directories...${NC}"
mkdir -p daily
mkdir -p pkm/daily
touch daily/.gitignore
touch pkm/daily/.gitignore

# Only try to deactivate if the command exists
if type deactivate >/dev/null 2>&1; then
    deactivate
fi

echo -e "${GREEN}✅ Installation complete! You can now run the application.${NC}"

# Ask if user wants to activate the virtual environment
read -p "$(echo -e ${YELLOW}❓ Do you want to activate the virtual environment now? \(Y/n\) ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo -e "${YELLOW}💡 To activate the virtual environment later, run: ${GREEN}source pkm_venv/bin/activate${NC}"
else
    echo -e "${BLUE}🚀 Activating virtual environment...${NC}"
    source pkm_venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated!${NC}"
fi
