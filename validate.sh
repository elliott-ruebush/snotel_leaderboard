#!/bin/bash
set -e

echo "🚀 Starting validation..."

# 1. Update data using Python backend
echo "📦 Fetching fresh data..."
cd backend
uv run src/generate_leaderboard.py
cd ..

# 2. Build frontend using Vite/TypeScript
echo "🏗️ Building frontend..."
cd frontend
npm run build
cd ..

echo "✅ Validation successful! The 'frontend/dist' folder is ready for deployment."
echo "💡 To view locally, you can run: cd frontend && npm run preview"
