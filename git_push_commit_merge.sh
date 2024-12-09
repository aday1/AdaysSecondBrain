#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VERSION_FILE=".version_tracker"

# Configure git to track file modes
git config core.fileMode true

# Function to initialize or read version numbers
init_versions() {
    if [ ! -f "$VERSION_FILE" ]; then
        echo "bleeding_edge=0.1.0" > "$VERSION_FILE"
        echo "ready_for_life=0.1.0" >> "$VERSION_FILE"
        echo "main=0.1.0" >> "$VERSION_FILE"
    fi
}

# Function to get current version for a branch
get_version() {
    local branch_prefix=$1
    local version=$(grep "^${branch_prefix}=" "$VERSION_FILE" | cut -d'=' -f2)
    if [ -z "$version" ]; then
        echo "0.1.0"
    else
        echo "$version"
    fi
}

# Function to increment version
increment_version() {
    local version=$1
    local major minor patch
    
    # Split version into components
    IFS='.' read -r major minor patch <<< "$version"
    
    # Increment patch version
    patch=$((patch + 1))
    
    # If patch reaches 1000, increment minor and reset patch
    if [ $patch -ge 1000 ]; then
        minor=$((minor + 1))
        patch=0
    fi
    
    # If minor reaches 10, increment major and reset minor
    if [ $minor -ge 10 ]; then
        major=$((major + 1))
        minor=0
    fi
    
    echo "$major.$minor.$patch"
}

# Function to update version in tracker file
update_version() {
    local branch_prefix=$1
    local new_version=$2
    local temp_file=$(mktemp)
    
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ $line == ${branch_prefix}=* ]]; then
            echo "${branch_prefix}=${new_version}"
        else
            echo "$line"
        fi
    done < "$VERSION_FILE" > "$temp_file"
    
    mv "$temp_file" "$VERSION_FILE"
}

# Function to check and update markdown documentation
check_markdown_docs() {
    echo -e "${GREEN}Checking markdown documentation...${NC}"
    
    # Array of required sections for each markdown file
    declare -A required_sections
    required_sections["README.md"]="# Description # Installation # Usage # Configuration"
    required_sections["QUICKSTART.md"]="# Quick Start Guide # Prerequisites # Setup # Running"
    required_sections["AI_GUIDE.md"]="# AI Integration Guide # Features # Implementation # Usage"
    required_sections["WISHLIST.md"]="# Wishlist # Planned Features # Improvements # Future Ideas"
    
    # Process each markdown file
    for md_file in *.md; do
        if [ -f "$md_file" ]; then
            echo "Checking $md_file..."
            
            # Create temp file for potential updates
            temp_file=$(mktemp)
            touch "$temp_file"
            
            # Check if file has a title header
            if ! grep -q "^# " "$md_file"; then
                echo "# ${md_file%.md}" > "$temp_file"
                echo "" >> "$temp_file"
                cat "$md_file" >> "$temp_file"
                mv "$temp_file" "$md_file"
                echo -e "${YELLOW}Added title header to $md_file${NC}"
            fi
            
            # Check for required sections based on file name
            if [[ ${required_sections[$md_file]} ]]; then
                missing_sections=false
                for section in ${required_sections[$md_file]}; do
                    if ! grep -q "^$section" "$md_file"; then
                        if [ "$missing_sections" = false ]; then
                            cp "$md_file" "$temp_file"
                            missing_sections=true
                        fi
                        echo "" >> "$temp_file"
                        echo "$section" >> "$temp_file"
                        echo "" >> "$temp_file"
                        echo "TODO: Add documentation for this section" >> "$temp_file"
                        echo -e "${YELLOW}Added missing section $section to $md_file${NC}"
                    fi
                done
                
                if [ "$missing_sections" = true ]; then
                    mv "$temp_file" "$md_file"
                fi
            fi
        fi
    done
    
    echo -e "${GREEN}Markdown documentation check completed!${NC}"
}

# Function to check for potential function breakage
check_functions() {
    local files_to_check=$(git diff --name-only)
    local has_warning=false

    for file in $files_to_check; do
        # Only check files that might contain functions (py, js, sh, etc.)
        if [[ $file =~ \.(py|js|sh|cpp|c|java|rb)$ ]]; then
            # Get the diff and look for function-related changes
            local diff_output=$(git diff $file)
            
            # Check for function removals or modifications
            if echo "$diff_output" | grep -E "^-[[:space:]]*(def|function|class|void|public|private)" > /dev/null; then
                echo -e "${YELLOW}WARNING: Potential function modification/removal detected in $file${NC}"
                echo "Affected lines:"
                echo "$diff_output" | grep -E "^[-+][[:space:]]*(def|function|class|void|public|private)" --color=always
                has_warning=true
            fi
        fi
    done

    if [ "$has_warning" = true ]; then
        echo -e "${YELLOW}⚠️  Function modifications detected! Please review the changes carefully.${NC}"
        read -p "Do you want to continue? (y/n): " continue_choice
        if [[ $continue_choice != "y" ]]; then
            echo -e "${RED}Operation aborted by user${NC}"
            exit 1
        fi
    fi
}

# Function to generate changes summary
generate_changes_summary() {
    local temp_file=$(mktemp)
    
    echo "Changed Files Summary:" > "$temp_file"
    echo "=====================" >> "$temp_file"
    echo "" >> "$temp_file"
    
    # Get list of changed files with status
    git status --porcelain | while read -r line; do
        local status=${line:0:2}
        local file=${line:3}
        
        case "$status" in
            "M "*)
                echo "Modified: $file" >> "$temp_file"
                echo "- Changes:" >> "$temp_file"
                git diff --unified=0 "$file" | grep "^+" | grep -v "^+++" | sed 's/^+/  /' >> "$temp_file"
                echo "" >> "$temp_file"
                ;;
            "A "*)
                echo "Added: $file" >> "$temp_file"
                echo "- New file added to the repository" >> "$temp_file"
                echo "" >> "$temp_file"
                ;;
            "D "*)
                echo "Deleted: $file" >> "$temp_file"
                echo "- File removed from the repository" >> "$temp_file"
                echo "" >> "$temp_file"
                ;;
        esac
    done
    
    echo "" >> "$temp_file"
    echo "Enter your commit message below:" >> "$temp_file"
    echo "--------------------------------" >> "$temp_file"
    echo "" >> "$temp_file"
    
    echo "$temp_file"
}

# Function to clean up unnecessary files
cleanup_repository() {
    echo -e "${GREEN}Cleaning up repository...${NC}"
    
    # Check and update markdown documentation
    check_markdown_docs
    
    # Set executable permissions on all shell scripts and update git
    echo -e "${GREEN}Setting executable permissions on shell scripts...${NC}"
    find . -type f -name "*.sh" -exec sh -c '
        chmod +x "$1"
        git update-index --chmod=+x "$1"
    ' sh {} \;
    
    # Comment out set -x in all shell scripts
    echo -e "${GREEN}Commenting out debug traces in shell scripts...${NC}"
    while IFS= read -r -d '' script; do
        echo "Processing $script..."
        # Create a temporary file
        temp_file=$(mktemp)
        
        # Process the file line by line
        while IFS= read -r line || [[ -n "$line" ]]; do
            # If line contains "set -x" and isn't already commented, comment it
            if [[ $line =~ ^[[:space:]]*set[[:space:]]-x[[:space:]]*$ ]] && [[ ! $line =~ ^[[:space:]]*# ]]; then
                echo "# $line" >> "$temp_file"
            else
                echo "$line" >> "$temp_file"
            fi
        done < "$script"
        
        # Replace original file with modified version
        mv "$temp_file" "$script"
    done < <(find . -type f -name "*.sh" -print0)
    
    # Remove Python compiled files
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type d -name "*.egg-info" -exec rm -rf {} +
    
    # Remove common backup files
    find . -type f -name "*~" -delete
    find . -type f -name "*.bak" -delete
    find . -type f -name "*.swp" -delete
    find . -type f -name ".DS_Store" -delete
    
    # Clean database backups (keep only the most recent)
    if [ -d "pkm/db/backups" ]; then
        cd pkm/db/backups
        # Keep only the most recent backup file
        ls -t | tail -n +2 | xargs -r rm --
        cd ../../..
    fi
    
    # Remove temporary files
    find . -type f -name "*.tmp" -delete
    find . -type f -name "*.temp" -delete
    
    # Remove log files if they exist
    find . -type f -name "*.log" -delete
    
    # Clean virtual environment if it exists
    if [ -d "venv" ]; then
        echo -e "${YELLOW}Virtual environment detected. Cleaning pip cache...${NC}"
        rm -rf venv/pip-selfcheck.json
        find venv -name "*.pyc" -delete
        find venv -name "__pycache__" -exec rm -rf {} +
    fi
    
    # Remove any Node.js related temporary files if they exist
    if [ -d "node_modules" ]; then
        echo -e "${YELLOW}Node.js modules detected. Cleaning npm cache...${NC}"
        rm -rf node_modules/.cache
    fi

    echo -e "${GREEN}Cleanup completed!${NC}"
}

# Initialize version tracking
init_versions

# Perform cleanup
cleanup_repository

# Show current status
echo -e "${GREEN}Current git status:${NC}"
git status

# Check if there are any changes
if ! git diff --quiet; then
    # Show diff
    echo -e "\n${GREEN}Changes to be committed:${NC}"
    git diff

    # Check for function breakage
    check_functions

    # Ask which branch to commit to
    while true; do
        echo -e "\n${GREEN}Select branch to commit and merge:${NC}"
        echo "1) Bleeding Edge (experimental features)"
        echo "2) Ready for Life (stable features)"
        echo "3) Main (production release)"
        read -p "Enter your choice (1, 2, or 3): " branch_choice
        
        case $branch_choice in
            1)
                branch_type="bleeding_edge"
                break
                ;;
            2)
                branch_type="ready_for_life"
                break
                ;;
            3)
                branch_type="main"
                echo -e "${YELLOW}⚠️  WARNING: You are about to merge to MAIN branch!${NC}"
                echo -e "${YELLOW}This should only be done for production-ready releases.${NC}"
                read -p "Are you absolutely sure? (yes/no): " main_confirm
                if [[ $main_confirm != "yes" ]]; then
                    echo -e "${RED}Main merge aborted${NC}"
                    exit 1
                fi
                break
                ;;
            *)
                echo -e "${RED}Invalid choice. Please enter 1, 2, or 3.${NC}"
                ;;
        esac
    done

    # Generate changes summary and get commit message using nano
    temp_file=$(generate_changes_summary)
    nano "$temp_file"
    commit_message=$(cat "$temp_file" | sed '/^Changed Files Summary:/,/^Enter your commit message below:$/d' | sed '/^--------------------------------$/d' | sed '/^$/d')
    rm "$temp_file"

    # Get and increment version for selected branch
    current_version=$(get_version "$branch_type")
    new_version=$(increment_version "$current_version")
    
    case "$branch_type" in
        "bleeding_edge")
            branch_name="bleeding-and-living-on-the-edge-v${new_version}"
            ;;
        "ready_for_life")
            branch_name="RDY_4_LIFE-v${new_version}"
            ;;
        "main")
            branch_name="main"
            ;;
    esac

    # Create and switch to selected branch
    if [ "$branch_type" = "main" ]; then
        echo -e "\n${GREEN}Switching to main branch...${NC}"
        git checkout main
        git pull origin main
    else
        echo -e "\n${GREEN}Creating branch: $branch_name${NC}"
        git checkout -b "$branch_name"
    fi

    git add .
    git commit -m "$commit_message"

    # Ask user if they want to push
    read -p "Do you want to push these changes? (y/n): " push_choice
    if [[ $push_choice == "y" ]]; then
        echo -e "\n${GREEN}Pushing branch...${NC}"
        git push origin "$branch_name"
        
        # Update version number after successful push
        update_version "$branch_type" "$new_version"
        
        echo -e "\n${GREEN}✅ Successfully pushed branch!${NC}"
        if [ "$branch_type" = "main" ]; then
            echo -e "Main branch updated to v${new_version}"
        else
            echo -e "New Version: v${new_version}"
        fi
    else
        echo -e "\n${YELLOW}Changes committed but not pushed${NC}"
    fi
else
    echo -e "${YELLOW}No changes detected in the repository${NC}"
fi
