#!/bin/bash

# Exit on error
set -e

# Verify we are in a git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ Error: Not a git repository."
  exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
if [ -z "$CURRENT_BRANCH" ]; then
  echo "❌ Error: Could not determine current branch."
  exit 1
fi

if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
  echo "⚠️ Warning: You are on '$CURRENT_BRANCH'. You should run this from a feature branch."
  read -p "Do you want to continue anyway? (y/N): " CONTINUE_MAIN
  if [[ ! "$CONTINUE_MAIN" =~ ^[Yy]$ ]]; then
    exit 0
  fi
fi

# Check for changes (both tracked and untracked, excluding ignored files)
CHANGES=$(git status --porcelain | grep -v '^\?\? data-pipeline/\.env') || true

if [ -z "$CHANGES" ]; then
  echo "ℹ️ No new changes to commit."
else
  echo "Staging changes..."
  # Stage everything except the .env file
  git add .
  
  # Prompt for commit message
  read -p "Enter commit message: " COMMIT_MSG
  if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="update: feature changes"
  fi
  
  echo "Committing changes..."
  git commit -m "$COMMIT_MSG"
fi

# Push to origin
echo "Pushing changes to origin/$CURRENT_BRANCH..."
git push -u origin "$CURRENT_BRANCH"

# Create Pull Request
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  echo "GitHub CLI found. Starting interactive PR creation..."
  gh pr create
else
  echo "Opening browser to create Pull Request..."
  PR_URL="https://github.com/NithinReddyJammula/food-sales-predictor/pull/new/$CURRENT_BRANCH"
  
  if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$PR_URL"
  elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open "$PR_URL"
  else
    echo "Please visit this URL to create your PR: $PR_URL"
  fi
fi
