#!/usr/bin/env bash
set -e

# Parse command line flags
SKIP_BUILD=false
for arg in "$@"; do
  case $arg in
    --no-build|--skip-build|-n)
      SKIP_BUILD=true
      shift
      ;;
  esac
done

# Load environment variables from .env.deploy if present
if [ -f .env.deploy ]; then
  export $(grep -v '^#' .env.deploy | xargs)
fi

# Verify required environment variables
if [ -z "$VPS_USER" ] || [ -z "$VPS_HOST" ] || [ -z "$VPS_PATH" ]; then
  echo "❌ Error: Missing configuration in .env.deploy"
  echo "Please make sure .env.deploy exists with VPS_USER, VPS_HOST, and VPS_PATH set."
  echo "See .env.deploy.example for reference."
  exit 1
fi

VPS_PORT="${VPS_PORT:-22}"

if [ "$SKIP_BUILD" = "true" ]; then
  echo "⏩ Skipping build step (--no-build)..."
  if [ ! -d "build" ]; then
    echo "❌ Error: build/ directory does not exist. Please run 'npm run build' first."
    exit 1
  fi
else
  export BASE_PATH="${BASE_PATH:-}"
  echo "🔨 Building site for VPS deployment (BASE_PATH='${BASE_PATH}')..."
  npm run build:app
fi

echo "🚀 Syncing build/ directory to VPS (${VPS_USER}@${VPS_HOST}:${VPS_PATH})..."
rsync -avz --delete -e "ssh -p ${VPS_PORT}" build/ ${VPS_USER}@${VPS_HOST}:${VPS_PATH}

echo "✅ Successfully deployed to VPS!"
