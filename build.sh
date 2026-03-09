#!/bin/bash

set -e  # Exit on error

echo "Building React frontend..."
cd frontend
npm run build
cd ..

echo "Creating backend/static directory if it doesn't exist..."
mkdir -p backend/static

echo "Copying built assets to backend/static..."
# Remove old static files if they exist
rm -rf backend/static/*
# Copy new build files
cp -r frontend/dist/* backend/static/

echo "Build and copy completed successfully!"
echo "Frontend assets are now in backend/static/"
