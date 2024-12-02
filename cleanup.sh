#!/bin/bash

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Starting cleanup...${NC}"

# Backup database if it exists
if [ -f "db/pkm.db" ]; then
    echo -e "${YELLOW}💾 Backing up database...${NC}"
    backup_dir="db/backups"
    mkdir -p "$backup_dir"
    cp db/pkm.db "$backup_dir/pkm.db.backup_$(date +%Y%m%d_%H%M%S)"
fi

# Remove Python bytecode files
echo -e "${BLUE}🗑️  Removing Python bytecode files...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

# Remove virtual environment
echo -e "${BLUE}🗑️  Removing virtual environment...${NC}"
rm -rf pkm_venv/

# Remove egg-info
echo -e "${BLUE}🗑️  Removing egg-info...${NC}"
rm -rf *.egg-info/

# Clean pkm_backup folders
echo -e "${YELLOW}📦 Cleaning PKM backup folders...${NC}"
read -p "$(echo -e ${YELLOW}❓ Do you want to remove all PKM backup folders? \(y/N\) ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🗑️  Removing PKM backup folders...${NC}"
    rm -rf pkm_backup_*/
fi

# Clean daily MD files
echo -e "${YELLOW}📝 Cleaning daily MD files...${NC}"
read -p "$(echo -e ${YELLOW}❓ Do you want to remove all daily log files? \(y/N\) ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🗑️  Removing daily logs...${NC}"
    rm -f daily/*.md
    rm -f pkm/daily/*.md
    # Keep .gitignore files
    touch daily/.gitignore
    touch pkm/daily/.gitignore
fi

# Clean database backups
echo -e "${YELLOW}🗄️  Cleaning database backups...${NC}"
read -p "$(echo -e ${YELLOW}❓ Do you want to remove all database backups? \(y/N\) ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🗑️  Removing database backups...${NC}"
    # Clean main db backups
    rm -f db/backups/*.db
    rm -f db/backups/*.backup*
    touch db/backups/.gitignore
    
    # Clean pkm db backups
    rm -f pkm/db/backups/*.db
    rm -f pkm/db/backups/*.backup*
    touch pkm/db/backups/.gitignore
    
    # Clean markdown backups
    rm -f pkm/db/md_backups/*.tar.gz
    rm -f pkm/db/md_backups/*.backup*
    mkdir -p pkm/db/md_backups
fi

# Remove database (optional)
read -p "$(echo -e ${YELLOW}❓ Do you want to remove the database? \(y/N\) ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}⚠️  Removing database...${NC}"
    rm -f db/pkm.db
    rm -f pkm/db/pkm.db
fi

echo -e "${GREEN}✨ Cleanup complete!${NC}"
