#!/bin/bash

# =============================================================================
# GitHub Secrets Cleanup Script
# =============================================================================
# This script allows you to clear all or selected GitHub Secrets
# Useful for migrations, cleanups, or starting fresh
#
# Usage: ./scripts/clear-secrets.sh [options]
# Options:
#   --all           Clear all secrets without prompting
#   --dry-run       Show what would be deleted without actually deleting
#   --exclude       Comma-separated list of secrets to keep
#   --pattern       Only delete secrets matching pattern (regex)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default options
DRY_RUN=false
DELETE_ALL=false
EXCLUDE_LIST=""
PATTERN=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            DELETE_ALL=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --exclude)
            EXCLUDE_LIST="$2"
            shift 2
            ;;
        --pattern)
            PATTERN="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --all           Clear all secrets without individual prompts"
            echo "  --dry-run       Show what would be deleted without actually deleting"
            echo "  --exclude LIST  Comma-separated list of secrets to keep"
            echo "  --pattern REGEX Only delete secrets matching pattern"
            echo "  --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Interactive mode"
            echo "  $0 --dry-run          # See what would be deleted"
            echo "  $0 --all              # Delete all secrets (with confirmation)"
            echo "  $0 --exclude DD_API_KEY,DD_APP_KEY"
            echo "  $0 --pattern '^SYNOLOGY_'"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

print_header() {
    echo -e "${CYAN}================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}================================${NC}"
    echo
}

print_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

prompt_yes_no() {
    local prompt="$1"
    local default="${2:-n}"
    
    if [[ "$default" == "y" ]]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi
    
    while true; do
        read -p "$prompt" yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            "" ) 
                if [[ "$default" == "y" ]]; then
                    return 0
                else
                    return 1
                fi
                ;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    # Check if GitHub CLI is installed
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is not installed"
        echo "Install it from: https://cli.github.com/"
        exit 1
    fi
    
    # Check if user is authenticated
    if ! gh auth status &> /dev/null; then
        print_warning "Not authenticated with GitHub CLI"
        echo "Run: gh auth login"
        exit 1
    fi
}

# Get repository info
get_repo_info() {
    REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
    if [[ -z "$REPO" ]]; then
        print_error "Could not determine repository. Are you in a git repository?"
        exit 1
    fi
    echo -e "${PURPLE}📦 Repository: $REPO${NC}"
    echo
}

# Convert comma-separated list to array
parse_exclude_list() {
    IFS=',' read -ra EXCLUDE_ARRAY <<< "$EXCLUDE_LIST"
    # Trim whitespace from each element
    for i in "${!EXCLUDE_ARRAY[@]}"; do
        EXCLUDE_ARRAY[$i]=$(echo "${EXCLUDE_ARRAY[$i]}" | xargs)
    done
}

# Check if secret should be excluded
should_exclude() {
    local secret="$1"
    
    # Check exclude list
    for excluded in "${EXCLUDE_ARRAY[@]}"; do
        if [[ "$secret" == "$excluded" ]]; then
            return 0
        fi
    done
    
    # Check pattern (if provided)
    if [[ -n "$PATTERN" ]]; then
        if ! [[ "$secret" =~ $PATTERN ]]; then
            return 0
        fi
    fi
    
    return 1
}

# Main function
main() {
    cd "$PROJECT_ROOT"
    
    if [[ "$DRY_RUN" == true ]]; then
        print_header "GitHub Secrets Cleanup (DRY RUN)"
        print_warning "This is a dry run - no secrets will be deleted"
    else
        print_header "GitHub Secrets Cleanup"
    fi
    
    # Check prerequisites
    check_prerequisites
    
    # Get repository info
    get_repo_info
    
    # Parse exclude list
    parse_exclude_list
    
    # Get list of all secrets
    print_step "Fetching current secrets..."
    SECRETS=$(gh secret list --repo "$REPO" --json name -q '.[].name' | sort)
    
    if [[ -z "$SECRETS" ]]; then
        print_success "No secrets found in repository"
        exit 0
    fi
    
    # Count secrets
    TOTAL_COUNT=$(echo "$SECRETS" | wc -l | xargs)
    echo -e "${BLUE}Found $TOTAL_COUNT secrets${NC}"
    echo
    
    # Build list of secrets to delete
    SECRETS_TO_DELETE=()
    SECRETS_TO_KEEP=()
    
    while IFS= read -r secret; do
        if should_exclude "$secret"; then
            SECRETS_TO_KEEP+=("$secret")
        else
            SECRETS_TO_DELETE+=("$secret")
        fi
    done <<< "$SECRETS"
    
    # Display categorized lists
    if [[ ${#SECRETS_TO_KEEP[@]} -gt 0 ]]; then
        echo -e "${GREEN}Secrets to KEEP (${#SECRETS_TO_KEEP[@]}):${NC}"
        for secret in "${SECRETS_TO_KEEP[@]}"; do
            echo "  ✓ $secret"
        done
        echo
    fi
    
    if [[ ${#SECRETS_TO_DELETE[@]} -eq 0 ]]; then
        print_success "No secrets match the deletion criteria"
        exit 0
    fi
    
    echo -e "${RED}Secrets to DELETE (${#SECRETS_TO_DELETE[@]}):${NC}"
    for secret in "${SECRETS_TO_DELETE[@]}"; do
        echo "  ✗ $secret"
    done
    echo
    
    # Group secrets by category for better visibility
    echo -e "${YELLOW}Grouped by category:${NC}"
    
    # Synology/Old Infrastructure
    SYNOLOGY_SECRETS=$(printf '%s\n' "${SECRETS_TO_DELETE[@]}" | grep -E '^SYNOLOGY_' || true)
    if [[ -n "$SYNOLOGY_SECRETS" ]]; then
        echo -e "${CYAN}  Synology (old):${NC}"
        echo "$SYNOLOGY_SECRETS" | sed 's/^/    - /'
    fi
    
    # GMKTec/New Infrastructure  
    GMKTEC_SECRETS=$(printf '%s\n' "${SECRETS_TO_DELETE[@]}" | grep -E '^GMKTEC_' || true)
    if [[ -n "$GMKTEC_SECRETS" ]]; then
        echo -e "${CYAN}  GMKTec (new):${NC}"
        echo "$GMKTEC_SECRETS" | sed 's/^/    - /'
    fi
    
    # Database
    DB_SECRETS=$(printf '%s\n' "${SECRETS_TO_DELETE[@]}" | grep -E '^(PG|SQLSERVER|MONGO)' || true)
    if [[ -n "$DB_SECRETS" ]]; then
        echo -e "${CYAN}  Database:${NC}"
        echo "$DB_SECRETS" | sed 's/^/    - /'
    fi
    
    # Datadog
    DD_SECRETS=$(printf '%s\n' "${SECRETS_TO_DELETE[@]}" | grep -E '^(DD_|DATADOG_)' || true)
    if [[ -n "$DD_SECRETS" ]]; then
        echo -e "${CYAN}  Datadog:${NC}"
        echo "$DD_SECRETS" | sed 's/^/    - /'
    fi
    
    # AWS/Amazon
    AWS_SECRETS=$(printf '%s\n' "${SECRETS_TO_DELETE[@]}" | grep -E '^(AMAZON_|AWS_|SES_)' || true)
    if [[ -n "$AWS_SECRETS" ]]; then
        echo -e "${CYAN}  AWS/Amazon:${NC}"
        echo "$AWS_SECRETS" | sed 's/^/    - /'
    fi
    
    # Tailscale
    TAILSCALE_SECRETS=$(printf '%s\n' "${SECRETS_TO_DELETE[@]}" | grep -E '^TAILSCALE_' || true)
    if [[ -n "$TAILSCALE_SECRETS" ]]; then
        echo -e "${CYAN}  Tailscale:${NC}"
        echo "$TAILSCALE_SECRETS" | sed 's/^/    - /'
    fi
    
    # Other APIs
    OTHER_SECRETS=$(printf '%s\n' "${SECRETS_TO_DELETE[@]}" | grep -vE '^(SYNOLOGY_|GMKTEC_|PG|SQLSERVER|MONGO|DD_|DATADOG_|AMAZON_|AWS_|SES_|TAILSCALE_)' || true)
    if [[ -n "$OTHER_SECRETS" ]]; then
        echo -e "${CYAN}  Other APIs:${NC}"
        echo "$OTHER_SECRETS" | sed 's/^/    - /'
    fi
    
    echo
    
    # Confirmation
    if [[ "$DRY_RUN" == true ]]; then
        print_success "Dry run complete - no changes made"
        echo
        echo "To actually delete these secrets, run without --dry-run:"
        echo "  $0"
        exit 0
    fi
    
    # Final confirmation
    echo -e "${RED}⚠️  WARNING: This action cannot be undone!${NC}"
    echo -e "${RED}   You are about to delete ${#SECRETS_TO_DELETE[@]} secrets.${NC}"
    echo
    
    if [[ "$DELETE_ALL" == true ]]; then
        if ! prompt_yes_no "Are you SURE you want to delete these ${#SECRETS_TO_DELETE[@]} secrets?" "n"; then
            print_warning "Deletion cancelled"
            exit 0
        fi
        
        # Double confirmation for safety
        echo
        echo -e "${RED}FINAL CONFIRMATION${NC}"
        echo -e "${RED}Type 'DELETE ALL SECRETS' to confirm:${NC}"
        read -r confirmation
        if [[ "$confirmation" != "DELETE ALL SECRETS" ]]; then
            print_warning "Deletion cancelled - confirmation text did not match"
            exit 0
        fi
    else
        # Interactive mode - ask for each secret
        echo "Interactive mode - confirm each secret deletion:"
        echo
        
        DELETED_COUNT=0
        SKIPPED_COUNT=0
        
        for secret in "${SECRETS_TO_DELETE[@]}"; do
            if prompt_yes_no "Delete $secret?" "n"; then
                print_step "Deleting $secret..."
                if gh secret delete "$secret" --repo "$REPO" 2>/dev/null; then
                    print_success "Deleted $secret"
                    ((DELETED_COUNT++))
                else
                    print_error "Failed to delete $secret"
                fi
            else
                print_warning "Skipped $secret"
                ((SKIPPED_COUNT++))
            fi
        done
        
        echo
        print_success "Cleanup complete!"
        echo "  Deleted: $DELETED_COUNT secrets"
        echo "  Skipped: $SKIPPED_COUNT secrets"
        echo "  Kept: ${#SECRETS_TO_KEEP[@]} secrets"
        exit 0
    fi
    
    # Bulk deletion (when --all is used)
    print_step "Deleting ${#SECRETS_TO_DELETE[@]} secrets..."
    echo
    
    DELETED_COUNT=0
    FAILED_COUNT=0
    
    for secret in "${SECRETS_TO_DELETE[@]}"; do
        echo -n "  Deleting $secret... "
        if gh secret delete "$secret" --repo "$REPO" 2>/dev/null; then
            echo -e "${GREEN}✓${NC}"
            ((DELETED_COUNT++))
        else
            echo -e "${RED}✗${NC}"
            ((FAILED_COUNT++))
        fi
    done
    
    echo
    print_success "Cleanup complete!"
    echo -e "${GREEN}  Successfully deleted: $DELETED_COUNT secrets${NC}"
    if [[ $FAILED_COUNT -gt 0 ]]; then
        echo -e "${RED}  Failed to delete: $FAILED_COUNT secrets${NC}"
    fi
    if [[ ${#SECRETS_TO_KEEP[@]} -gt 0 ]]; then
        echo -e "${BLUE}  Kept (excluded): ${#SECRETS_TO_KEEP[@]} secrets${NC}"
    fi
    
    echo
    echo -e "${CYAN}Next steps:${NC}"
    echo "1. Run './scripts/setup-secrets.sh .env' to upload new secrets"
    echo "2. Verify secrets at: https://github.com/$REPO/settings/secrets/actions"
    echo "3. Test your deployment workflow"
}

# Run main function
main
