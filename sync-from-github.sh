#!/bin/bash
# Sync local repository with GitHub (resolve divergent branches)

set -e

echo "========================================"
echo "  SYNC WITH GITHUB"
echo "========================================"
echo ""

BRANCH="claude/add-ocr-email-extraction-01E2J9RkrixaT8TUTReBnHiG"

echo "=== Step 1: Fetch latest changes from GitHub ==="
git fetch origin $BRANCH
echo "✅ Fetched latest changes"

echo ""
echo "=== Step 2: Check for local changes ==="
if git diff-index --quiet HEAD --; then
    echo "✅ No local changes detected"
    HAS_LOCAL_CHANGES=false
else
    echo "⚠️  Warning: You have local uncommitted changes"
    echo ""
    git status --short
    echo ""
    read -p "Stash local changes before syncing? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git stash
        echo "✅ Local changes stashed"
        HAS_LOCAL_CHANGES=true
    else
        echo "❌ Cannot proceed with uncommitted changes. Commit or stash them first."
        exit 1
    fi
fi

echo ""
echo "=== Step 3: Check commit history ==="
LOCAL_COMMITS=$(git rev-list HEAD ^origin/$BRANCH --count 2>/dev/null || echo "0")
REMOTE_COMMITS=$(git rev-list origin/$BRANCH ^HEAD --count 2>/dev/null || echo "0")

echo "Local commits ahead: $LOCAL_COMMITS"
echo "Remote commits ahead: $REMOTE_COMMITS"

echo ""
if [ "$LOCAL_COMMITS" -eq 0 ] && [ "$REMOTE_COMMITS" -gt 0 ]; then
    echo "=== Step 4: Fast-forward to remote (simple update) ==="
    git merge --ff-only origin/$BRANCH
    echo "✅ Updated to latest version"

elif [ "$LOCAL_COMMITS" -gt 0 ] && [ "$REMOTE_COMMITS" -gt 0 ]; then
    echo "=== Step 4: Divergent branches detected ==="
    echo ""
    echo "Your local branch has $LOCAL_COMMITS commit(s) that are not on GitHub"
    echo "GitHub has $REMOTE_COMMITS new commit(s) from the development session"
    echo ""
    echo "Options:"
    echo "  1) Rebase - Apply your local changes on top of GitHub changes (recommended)"
    echo "  2) Reset - Discard local commits and use GitHub version (DESTRUCTIVE)"
    echo "  3) Merge - Create merge commit (can cause conflicts)"
    echo ""
    read -p "Choose option (1/2/3): " -n 1 -r
    echo

    if [[ $REPLY == "1" ]]; then
        echo "Rebasing local commits on top of GitHub..."
        git rebase origin/$BRANCH
        echo "✅ Rebase complete"

    elif [[ $REPLY == "2" ]]; then
        echo "⚠️  WARNING: This will discard your local commits!"
        read -p "Are you sure? Type 'yes' to confirm: " CONFIRM
        if [ "$CONFIRM" = "yes" ]; then
            git reset --hard origin/$BRANCH
            echo "✅ Reset to match GitHub"
        else
            echo "❌ Cancelled"
            exit 1
        fi

    elif [[ $REPLY == "3" ]]; then
        echo "Creating merge commit..."
        git merge origin/$BRANCH
        echo "✅ Merge complete"

    else
        echo "❌ Invalid option"
        exit 1
    fi

elif [ "$LOCAL_COMMITS" -gt 0 ] && [ "$REMOTE_COMMITS" -eq 0 ]; then
    echo "=== Step 4: Local is ahead of remote ==="
    echo "✅ Already up to date (you have newer commits locally)"

else
    echo "=== Step 4: Already up to date ==="
    echo "✅ Nothing to sync"
fi

echo ""
if [ "$HAS_LOCAL_CHANGES" = true ]; then
    echo "=== Step 5: Restore stashed changes ==="
    read -p "Apply stashed changes now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git stash pop
        echo "✅ Stashed changes restored"
    else
        echo "⏭️  Stashed changes kept (run 'git stash pop' to restore later)"
    fi
fi

echo ""
echo "=== Step 6: Show current status ==="
git log --oneline -5
echo ""
git status

echo ""
echo "========================================"
echo "  ✅ SYNC COMPLETE"
echo "========================================"
echo ""
echo "Latest commits from GitHub are now in your local repository."
echo ""
echo "Next steps:"
echo "  1. Rebuild containers: bash rebuild-containers.sh"
echo "  2. Check application: http://agenticrag360.com"
echo ""
