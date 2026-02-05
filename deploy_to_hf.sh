#!/bin/bash

# Quick Start Script for Hugging Face Deployment
# This script helps you quickly deploy to Hugging Face Spaces

echo "🍯 Hugging Face Spaces Deployment Helper"
echo "==========================================="
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    echo "✅ Git initialized"
else
    echo "✅ Git repository already initialized"
fi

echo ""
echo "📝 Please enter your Hugging Face details:"
read -p "Username: " HF_USERNAME
read -p "Space name: " HF_SPACE_NAME

echo ""
echo "🔧 Setting up Hugging Face remote..."

# Check if 'hf' remote already exists
if git remote get-url hf > /dev/null 2>&1; then
    echo "⚠️  Remote 'hf' already exists. Removing..."
    git remote remove hf
fi

# Add HF remote
git remote add hf https://huggingface.co/spaces/$HF_USERNAME/$HF_SPACE_NAME
echo "✅ Remote added: https://huggingface.co/spaces/$HF_USERNAME/$HF_SPACE_NAME"

echo ""
echo "📄 Preparing README for Hugging Face..."

# Backup original README if it exists and HF_README doesn't
if [ -f "README.md" ] && [ ! -f "README_PROJECT.md" ]; then
    mv README.md README_PROJECT.md
    echo "✅ Backed up original README to README_PROJECT.md"
fi

# Copy HF README
if [ -f "HF_README.md" ]; then
    cp HF_README.md README.md
    echo "✅ Using HF_README.md as README.md"
else
    echo "❌ HF_README.md not found!"
    exit 1
fi

echo ""
echo "📦 Staging files for commit..."
git add .

echo ""
read -p "Commit message (default: 'Initial deployment to Hugging Face'): " COMMIT_MSG
COMMIT_MSG=${COMMIT_MSG:-"Initial deployment to Hugging Face"}

echo ""
echo "💾 Committing changes..."
git commit -m "$COMMIT_MSG"

echo ""
echo "🚀 Pushing to Hugging Face Spaces..."
echo "Note: You may be prompted for your Hugging Face credentials"
echo ""

# Determine the default branch
DEFAULT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "main")

git push hf $DEFAULT_BRANCH

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Your Space will be available at:"
echo "   https://$HF_USERNAME-$HF_SPACE_NAME.hf.space"
echo ""
echo "📖 API Documentation:"
echo "   https://$HF_USERNAME-$HF_SPACE_NAME.hf.space/docs"
echo ""
echo "⏳ Please allow 2-5 minutes for the Space to build and deploy."
echo ""
echo "📊 Monitor your deployment at:"
echo "   https://huggingface.co/spaces/$HF_USERNAME/$HF_SPACE_NAME"
echo ""
echo "Happy deploying! 🎉"
