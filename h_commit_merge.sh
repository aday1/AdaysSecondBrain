[1mdiff --git a/git_push_commit_merge.sh b/git_push_commit_merge.sh[m
[1mindex 268ea42..45b9a9f 100755[m
[1m--- a/git_push_commit_merge.sh[m
[1m+++ b/git_push_commit_merge.sh[m
[36m@@ -70,6 +70,28 @@[m [mupdate_version() {[m
     mv "$temp_file" "$VERSION_FILE"[m
 }[m
 [m
[32m+[m[32m# Function to comment out set -x in bash files[m
[32m+[m[32mcomment_set_x() {[m
[32m+[m[32m    local file=$1[m
[32m+[m[32m    if [ -f "$file" ]; then[m
[32m+[m[32m        # Create a temporary file[m
[32m+[m[32m        local temp_file=$(mktemp)[m
[32m+[m[41m        [m
[32m+[m[32m        # Process the file line by line[m
[32m+[m[32m        while IFS= read -r line || [[ -n "$line" ]]; do[m
[32m+[m[32m            # If line contains "set -x" and isn't already commented, comment it[m
[32m+[m[32m            if [[ $line =~ ^[[:space:]]*set[[:space:]]-x[[:space:]]*$ ]]; then[m
[32m+[m[32m                echo "# $line" >> "$temp_file"[m
[32m+[m[32m            else[m
[32m+[m[32m                echo "$line" >> "$temp_file"[m
[32m+[m[32m            fi[m
[32m+[m[32m        done < "$file"[m
[32m+[m[41m        [m
[32m+[m[32m        # Replace original file with modified version[m
[32m+[m[32m        mv "$temp_file" "$file"[m
[32m+[m[32m    fi[m
[32m+[m[32m}[m
[32m+[m
 # Function to check for potential function breakage[m
 check_functions() {[m
     local files_to_check=$(git diff --name-only)[m
[36m@@ -105,6 +127,10 @@[m [mcheck_functions() {[m
 cleanup_repository() {[m
     echo -e "${GREEN}Cleaning up repository...${NC}"[m
     [m
[32m+[m[32m    # Comment out set -x in all shell scripts[m
[32m+[m[32m    echo -e "${GREEN}Commenting out debug traces in shell scripts...${NC}"[m
[32m+[m[32m    find . -type f -name "*.sh" -exec bash -c 'comment_set_x "$0"' {} \;[m
[32m+[m[41m    [m
     # Remove Python compiled files[m
     find . -type f -name "*.pyc" -delete[m
     find . -type f -name "*.pyo" -delete[m
