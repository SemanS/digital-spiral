#!/usr/bin/env bash
# Implementation script for Spec-Driven Development
# This script executes all tasks from tasks.md in the correct order

set -euo pipefail

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get repository root
REPO_ROOT=$(get_repo_root)
FEATURE_DIR="$REPO_ROOT/.specify/features"

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓ ${NC}$1"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${NC}$1"
}

print_error() {
    echo -e "${RED}✗ ${NC}$1"
}

# Function to find the current feature
find_current_feature() {
    # Check SPECIFY_FEATURE environment variable first
    if [[ -n "${SPECIFY_FEATURE:-}" ]]; then
        echo "$SPECIFY_FEATURE"
        return
    fi
    
    # Try to get from git branch
    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        local branch=$(git rev-parse --abbrev-ref HEAD)
        if [[ "$branch" != "main" && "$branch" != "master" ]]; then
            echo "$branch"
            return
        fi
    fi
    
    # Find latest feature directory
    local latest_feature=""
    local highest=0
    
    for dir in "$FEATURE_DIR"/*; do
        if [[ -d "$dir" ]]; then
            local dirname=$(basename "$dir")
            if [[ "$dirname" =~ ^([0-9]{3})- ]]; then
                local number=${BASH_REMATCH[1]}
                number=$((10#$number))
                if [[ "$number" -gt "$highest" ]]; then
                    highest=$number
                    latest_feature=$dirname
                fi
            fi
        fi
    done
    
    echo "$latest_feature"
}

# Function to validate prerequisites
validate_prerequisites() {
    local feature=$1
    local feature_path="$FEATURE_DIR/$feature"
    
    print_info "Validating prerequisites for feature: $feature"
    
    # Check if feature directory exists
    if [[ ! -d "$feature_path" ]]; then
        print_error "Feature directory not found: $feature_path"
        return 1
    fi
    
    # Check required files
    local required_files=("constitution.md" "spec.md" "plan.md" "tasks.md")
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$feature_path/$file" ]]; then
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        print_error "Missing required files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        return 1
    fi
    
    print_success "All prerequisites validated"
    return 0
}

# Function to parse tasks from tasks.md
parse_tasks() {
    local feature=$1
    local tasks_file="$FEATURE_DIR/$feature/tasks.md"
    
    print_info "Parsing tasks from: $tasks_file"
    
    # Extract task headers (#### Task X.Y: Task Name)
    local tasks=$(grep -E "^#### Task [0-9]+\.[0-9]+:" "$tasks_file" | sed 's/^#### //')
    
    if [[ -z "$tasks" ]]; then
        print_error "No tasks found in tasks.md"
        return 1
    fi
    
    local task_count=$(echo "$tasks" | wc -l | tr -d ' ')
    print_success "Found $task_count tasks"
    
    echo "$tasks"
}

# Function to extract task details
extract_task_details() {
    local feature=$1
    local task_id=$2
    local tasks_file="$FEATURE_DIR/$feature/tasks.md"
    
    # Extract task section
    local task_section=$(awk "/^#### Task $task_id:/,/^#### Task [0-9]+\.[0-9]+:|^## Phase [0-9]+:|^## Summary/" "$tasks_file")
    
    # Extract effort
    local effort=$(echo "$task_section" | grep "^\*\*Effort\*\*:" | sed 's/^\*\*Effort\*\*: //')
    
    # Extract dependencies
    local dependencies=$(echo "$task_section" | grep "^\*\*Dependencies\*\*:" | sed 's/^\*\*Dependencies\*\*: //')
    
    # Extract priority
    local priority=$(echo "$task_section" | grep "^\*\*Priority\*\*:" | sed 's/^\*\*Priority\*\*: //')
    
    # Extract acceptance criteria count
    local criteria_count=$(echo "$task_section" | grep -c "^- \[ \]" || echo "0")
    
    echo "Effort: $effort"
    echo "Dependencies: $dependencies"
    echo "Priority: $priority"
    echo "Acceptance Criteria: $criteria_count"
}

# Function to check if task dependencies are met
check_dependencies() {
    local dependencies=$1
    local completed_tasks=$2
    
    if [[ "$dependencies" == "None" ]]; then
        return 0
    fi
    
    # Parse dependencies (e.g., "Task 1.1, Task 1.2")
    IFS=',' read -ra deps <<< "$dependencies"
    
    for dep in "${deps[@]}"; do
        dep=$(echo "$dep" | xargs) # Trim whitespace
        dep=$(echo "$dep" | sed 's/Task //')
        
        if ! echo "$completed_tasks" | grep -q "$dep"; then
            print_warning "Dependency not met: Task $dep"
            return 1
        fi
    done
    
    return 0
}

# Function to execute a single task
execute_task() {
    local feature=$1
    local task_id=$2
    local task_name=$3
    
    print_info "Executing Task $task_id: $task_name"
    
    # Extract task details
    local details=$(extract_task_details "$feature" "$task_id")
    echo "$details"
    
    # Here you would call Auggie or another AI agent to implement the task
    # For now, we'll just print a message
    print_warning "Task execution requires AI agent integration"
    print_info "To execute this task, run:"
    echo ""
    echo "  Auggie, implement Task $task_id: $task_name"
    echo ""
    echo "  Follow the acceptance criteria in:"
    echo "  .specify/features/$feature/tasks.md"
    echo ""
    
    # Ask user if task is complete
    read -p "Is Task $task_id complete? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_success "Task $task_id marked as complete"
        return 0
    else
        print_error "Task $task_id not complete"
        return 1
    fi
}

# Main implementation function
implement() {
    print_info "Starting implementation process..."
    echo ""
    
    # Find current feature
    local feature=$(find_current_feature)
    
    if [[ -z "$feature" ]]; then
        print_error "Could not determine current feature"
        print_info "Set SPECIFY_FEATURE environment variable or create a feature branch"
        exit 1
    fi
    
    print_info "Current feature: $feature"
    echo ""
    
    # Validate prerequisites
    if ! validate_prerequisites "$feature"; then
        exit 1
    fi
    echo ""
    
    # Parse tasks
    local tasks=$(parse_tasks "$feature")
    echo ""
    
    # Track completed tasks
    local completed_tasks=""
    
    # Execute tasks
    while IFS= read -r task_line; do
        # Extract task ID and name
        local task_id=$(echo "$task_line" | sed -E 's/Task ([0-9]+\.[0-9]+):.*/\1/')
        local task_name=$(echo "$task_line" | sed -E 's/Task [0-9]+\.[0-9]+: (.*)/\1/')
        
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # Check dependencies
        local details=$(extract_task_details "$feature" "$task_id")
        local dependencies=$(echo "$details" | grep "^Dependencies:" | sed 's/Dependencies: //')
        
        if ! check_dependencies "$dependencies" "$completed_tasks"; then
            print_warning "Skipping Task $task_id due to unmet dependencies"
            continue
        fi
        
        # Execute task
        if execute_task "$feature" "$task_id" "$task_name"; then
            completed_tasks="$completed_tasks $task_id"
        else
            print_error "Implementation stopped at Task $task_id"
            exit 1
        fi
        
    done <<< "$tasks"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_success "Implementation complete!"
    echo ""
    print_info "Next steps:"
    echo "  1. Run tests: pytest tests/ -v --cov"
    echo "  2. Check types: mypy src/"
    echo "  3. Lint code: ruff check src/"
    echo "  4. Create PR: gh pr create"
}

# Run implementation
implement

