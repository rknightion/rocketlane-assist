#!/bin/bash

# Script to upload sourcemaps to Grafana Faro
# This should be run after building the production bundle
# 
# Usage: ./upload-sourcemaps.sh
# Or: FARO_SOURCEMAP_API_KEY=your-api-key ./upload-sourcemaps.sh

set -e

# Check if API key is provided
if [ -z "$FARO_SOURCEMAP_API_KEY" ]; then
  # Try to load from .env file if it exists
  if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
  fi
  
  # Check again after loading .env
  if [ -z "$FARO_SOURCEMAP_API_KEY" ]; then
    echo "Error: FARO_SOURCEMAP_API_KEY environment variable is not set"
    echo "Please set it before running this script:"
    echo "export FARO_SOURCEMAP_API_KEY=\"your-api-key\""
    exit 1
  fi
fi

# Configuration
APP_NAME="rocketlane-assistant"
ENDPOINT="https://faro-api-prod-gb-south-1.grafana.net/faro/api/v1"
APP_ID="193"
STACK_ID="1217581"

# Check if dist directory exists
if [ ! -d "dist" ]; then
  echo "Error: dist directory not found. Please run 'npm run build' first."
  exit 1
fi

# Check if sourcemaps exist
if ! ls dist/assets/*.js.map 1> /dev/null 2>&1; then
  echo "Error: No sourcemaps found in dist/assets directory"
  exit 1
fi

# Generate a unique bundle ID based on timestamp
BUNDLE_ID=$(date +%s)

echo "Uploading sourcemaps to Grafana Faro..."
echo "App: $APP_NAME (ID: $APP_ID, Stack: $STACK_ID)"
echo "Bundle ID: $BUNDLE_ID"
echo ""

# First, inject the bundle ID into the JS files
echo "Injecting bundle ID into JS files..."
npx @grafana/faro-cli inject-bundle-id \
  --bundle-id="$BUNDLE_ID" \
  --app-name="$APP_NAME" \
  --files 'dist/assets/*.js'

# Now upload the sourcemaps with the bundle ID
echo "Uploading sourcemaps..."
npx @grafana/faro-cli upload \
  --endpoint="$ENDPOINT" \
  --app-id="$APP_ID" \
  --api-key="$FARO_SOURCEMAP_API_KEY" \
  --stack-id="$STACK_ID" \
  --bundle-id="$BUNDLE_ID" \
  --output-path="dist/assets" \
  --app-name="$APP_NAME" \
  --keep-sourcemaps \
  --verbose

echo ""
echo "✓ Sourcemap upload complete!"