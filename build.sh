#!/bin/bash
# Build script for Railway deployment
# Builds frontend and copies to backend static directory

set -e

echo "=== Building Paris 2026 Marathon Tracker ==="

# Build frontend
echo "Building frontend..."
cd frontend
npm install
npm run build

# Copy built files to backend static directory
echo "Copying frontend to backend/app/static..."
rm -rf ../backend/app/static
mkdir -p ../backend/app/static
cp -r dist/* ../backend/app/static/

echo "Build complete!"
echo "Static files are in backend/app/static/"
