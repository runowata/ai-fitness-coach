#!/bin/bash

# GitHub Labels Setup Script
# Requirements: gh CLI tool and jq

set -e

# Check requirements
command -v gh >/dev/null 2>&1 || { echo "Error: gh CLI required. Install from: https://cli.github.com/"; exit 1; }
command -v yq >/dev/null 2>&1 || { echo "Error: yq required. Install: brew install yq"; exit 1; }

# Get repo info
OWNER=$(gh repo view --json owner --jq .owner.login 2>/dev/null || echo "")
REPO=$(gh repo view --json name --jq .name 2>/dev/null || echo "")

if [[ -z "$OWNER" || -z "$REPO" ]]; then
    echo "Error: Not in a GitHub repository or gh not authenticated"
    echo "Run: gh auth login"
    exit 1
fi

echo "Setting up labels for $OWNER/$REPO..."

# Process labels from YAML file
yq -c '.[]' .github/labels.yml 2>/dev/null | while IFS= read -r label; do
    NAME=$(echo "$label" | jq -r '.name')
    COLOR=$(echo "$label" | jq -r '.color')
    DESC=$(echo "$label" | jq -r '.description // ""')
    
    echo "Processing: $NAME"
    
    # Try to create, fallback to update if exists
    if gh api -X POST "repos/$OWNER/$REPO/labels" \
        -f name="$NAME" -f color="$COLOR" -f description="$DESC" \
        --silent 2>/dev/null; then
        echo "  ✅ Created: $NAME"
    else
        # Update existing label
        if gh api -X PATCH "repos/$OWNER/$REPO/labels/$(printf %s "$NAME" | jq -sRr @uri)" \
            -f new_name="$NAME" -f color="$COLOR" -f description="$DESC" \
            --silent 2>/dev/null; then
            echo "  🔄 Updated: $NAME"
        else
            echo "  ❌ Failed: $NAME"
        fi
    fi
done

echo ""
echo "🎉 GitHub labels setup complete!"
echo "View at: https://github.com/$OWNER/$REPO/labels"