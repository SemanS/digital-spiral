#!/usr/bin/env bash
# Validation script for Spec-Driven Development features
# Checks if all required files exist and are valid

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

# Function to validate a single feature
validate_feature() {
    local feature=$1
    local feature_path="$FEATURE_DIR/$feature"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_info "Validating feature: $feature"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check if feature directory exists
    if [[ ! -d "$feature_path" ]]; then
        print_error "Feature directory not found: $feature_path"
        return 1
    fi
    print_success "Feature directory exists"
    
    # Check required files
    local required_files=("constitution.md" "spec.md" "plan.md" "tasks.md" "README.md")
    local missing_files=()
    local valid_files=0
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$feature_path/$file" ]]; then
            missing_files+=("$file")
            print_error "Missing: $file"
        else
            # Check if file is not empty
            if [[ -s "$feature_path/$file" ]]; then
                local size=$(wc -c < "$feature_path/$file" | tr -d ' ')
                print_success "Found: $file (${size} bytes)"
                ((valid_files++))
            else
                print_warning "Empty: $file"
            fi
        fi
    done
    
    # Check optional files
    local optional_files=("AUGGIE_GUIDE.md" "LLM_SQL_ANALYTICS_SUMMARY.md" "LLM_SQL_ANALYTICS_QUICKSTART.md")
    for file in "${optional_files[@]}"; do
        if [[ -f "$feature_path/$file" ]]; then
            local size=$(wc -c < "$feature_path/$file" | tr -d ' ')
            print_info "Optional: $file (${size} bytes)"
        fi
    done
    
    echo ""
    
    # Validate constitution.md
    if [[ -f "$feature_path/constitution.md" ]]; then
        print_info "Validating constitution.md..."
        local has_principles=$(grep -c "## Architecture Philosophy\|## Principles" "$feature_path/constitution.md" || echo "0")
        local has_tech_stack=$(grep -c "## Technology Stack\|## Tech Stack" "$feature_path/constitution.md" || echo "0")
        
        if [[ $has_principles -gt 0 ]]; then
            print_success "  - Has architecture principles"
        else
            print_warning "  - Missing architecture principles"
        fi
        
        if [[ $has_tech_stack -gt 0 ]]; then
            print_success "  - Has technology stack"
        else
            print_warning "  - Missing technology stack"
        fi
    fi
    
    # Validate spec.md
    if [[ -f "$feature_path/spec.md" ]]; then
        print_info "Validating spec.md..."
        local user_stories=$(grep -c "^### US[0-9]\+:" "$feature_path/spec.md" || echo "0")
        local requirements=$(grep -c "## Requirements\|## Technical Requirements" "$feature_path/spec.md" || echo "0")
        
        print_success "  - Found $user_stories user stories"
        
        if [[ $requirements -gt 0 ]]; then
            print_success "  - Has requirements section"
        else
            print_warning "  - Missing requirements section"
        fi
    fi
    
    # Validate plan.md
    if [[ -f "$feature_path/plan.md" ]]; then
        print_info "Validating plan.md..."
        local phases=$(grep -c "^## Phase [0-9]\+:" "$feature_path/plan.md" || echo "0")
        local database=$(grep -c "## Database Schema\|## Data Model" "$feature_path/plan.md" || echo "0")
        
        print_success "  - Found $phases implementation phases"
        
        if [[ $database -gt 0 ]]; then
            print_success "  - Has database schema"
        else
            print_warning "  - Missing database schema"
        fi
    fi
    
    # Validate tasks.md
    if [[ -f "$feature_path/tasks.md" ]]; then
        print_info "Validating tasks.md..."
        local tasks=$(grep -c "^#### Task [0-9]\+\.[0-9]\+:" "$feature_path/tasks.md" || echo "0")
        local acceptance=$(grep -c "^\*\*Acceptance Criteria\*\*:" "$feature_path/tasks.md" || echo "0")
        
        print_success "  - Found $tasks tasks"
        print_success "  - Found $acceptance acceptance criteria sections"
    fi
    
    echo ""
    
    # Summary
    if [[ ${#missing_files[@]} -eq 0 ]]; then
        print_success "Feature validation PASSED: All required files present"
        return 0
    else
        print_error "Feature validation FAILED: Missing ${#missing_files[@]} required files"
        return 1
    fi
}

# Main validation function
validate_all() {
    print_info "Starting feature validation..."
    echo ""
    
    # Check if .specify directory exists
    if [[ ! -d "$FEATURE_DIR" ]]; then
        print_error ".specify/features directory not found"
        exit 1
    fi
    
    # Find all features
    local features=()
    for dir in "$FEATURE_DIR"/*; do
        if [[ -d "$dir" ]]; then
            local dirname=$(basename "$dir")
            if [[ "$dirname" =~ ^[0-9]{3}- ]]; then
                features+=("$dirname")
            fi
        fi
    done
    
    if [[ ${#features[@]} -eq 0 ]]; then
        print_warning "No features found in $FEATURE_DIR"
        exit 0
    fi
    
    print_info "Found ${#features[@]} features"
    
    # Validate each feature
    local passed=0
    local failed=0
    
    for feature in "${features[@]}"; do
        if validate_feature "$feature"; then
            ((passed++))
        else
            ((failed++))
        fi
    done
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_info "Validation Summary"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_success "Passed: $passed"
    if [[ $failed -gt 0 ]]; then
        print_error "Failed: $failed"
    fi
    echo ""
    
    if [[ $failed -eq 0 ]]; then
        print_success "All features validated successfully! ✨"
        return 0
    else
        print_error "Some features failed validation"
        return 1
    fi
}

# Run validation
validate_all

