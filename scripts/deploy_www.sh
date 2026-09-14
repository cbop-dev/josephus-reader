#!/usr/bin/env bash
set -e

# Parse command line flags
SKIP_BUILD=false
PROMOTE=false
ROLLBACK=false
SHOW_HISTORY=false

for arg in "$@"; do
  case $arg in
    --no-build|--skip-build|-n)
      SKIP_BUILD=true
      shift
      ;;
    --promote)
      PROMOTE=true
      shift
      ;;
    --rollback)
      ROLLBACK=true
      shift
      ;;
    --history)
      SHOW_HISTORY=true
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
VPS_ROOT="${VPS_PATH%/}" # Remove trailing slash if present
SSH_CMD="ssh -p ${VPS_PORT} ${VPS_USER}@${VPS_HOST}"

# -------------------------------------------------------------
# MODE: SHOW DEPLOYMENT HISTORY
# -------------------------------------------------------------
if [ "$SHOW_HISTORY" = "true" ]; then
  echo "📜 Live Deployment History Stack (${VPS_ROOT}/live_history.txt):"
  $SSH_CMD bash -s <<EOF
    if [ -f ${VPS_ROOT}/live_history.txt ] && [ -s ${VPS_ROOT}/live_history.txt ]; then
      cat ${VPS_ROOT}/live_history.txt
    else
      echo "(No history recorded yet)"
    fi
    echo ""
    echo "Active Live Target  (current) : \$(readlink -f ${VPS_ROOT}/current 2>/dev/null || echo 'None')"
    echo "Active Staging Target (staging) : \$(readlink -f ${VPS_ROOT}/staging 2>/dev/null || echo 'None')"
EOF
  exit 0
fi

# -------------------------------------------------------------
# MODE 1: ROLLBACK LIVE SITE TO PREVIOUS STACK RELEASE
# -------------------------------------------------------------
if [ "$ROLLBACK" = "true" ]; then
  echo "🔄 Rolling back live deployment using history stack..."
  $SSH_CMD bash -s <<EOF
    set -e
    HISTORY_FILE="${VPS_ROOT}/live_history.txt"
    CURRENT_TARGET=\$(readlink -f ${VPS_ROOT}/current 2>/dev/null || true)
    
    if [ ! -f "\$HISTORY_FILE" ] || [ ! -s "\$HISTORY_FILE" ]; then
      echo "❌ Error: No previous live releases recorded in live_history.txt."
      exit 1
    fi
    
    TARGET_RELEASE=""
    while [ -s "\$HISTORY_FILE" ]; do
      CANDIDATE=\$(tail -n 1 "\$HISTORY_FILE")
      # Pop the last line
      sed -i '\$d' "\$HISTORY_FILE"
      
      if [ -n "\$CANDIDATE" ] && [ -d "\$CANDIDATE" ] && [ "\$CANDIDATE" != "\$CURRENT_TARGET" ]; then
        TARGET_RELEASE="\$CANDIDATE"
        break
      fi
    done
    
    if [ -z "\$TARGET_RELEASE" ] || [ ! -d "\$TARGET_RELEASE" ]; then
      echo "❌ Error: No valid previous release directory found in history stack."
      exit 1
    fi
    
    # Point current to target release
    ln -sfn "\$TARGET_RELEASE" ${VPS_ROOT}/current
    if [ -n "\$CURRENT_TARGET" ]; then
      ln -sfn "\$CURRENT_TARGET" ${VPS_ROOT}/previous
    fi
    
    echo "✅ Successfully rolled back live site to \$(basename \$TARGET_RELEASE)!"
EOF
  exit 0
fi

# -------------------------------------------------------------
# MODE 2: PROMOTE STAGING TO LIVE
# -------------------------------------------------------------
if [ "$PROMOTE" = "true" ]; then
  echo "🚀 Promoting staging build to live site..."
  $SSH_CMD bash -s <<EOF
    set -e
    HISTORY_FILE="${VPS_ROOT}/live_history.txt"
    STAGING_TARGET=\$(readlink -f ${VPS_ROOT}/staging 2>/dev/null || true)
    CURRENT_TARGET=\$(readlink -f ${VPS_ROOT}/current 2>/dev/null || true)
    
    if [ -z "\$STAGING_TARGET" ] || [ ! -d "\$STAGING_TARGET" ]; then
      echo "❌ Error: Staging target (${VPS_ROOT}/staging) does not exist or is not a valid directory."
      exit 1
    fi
    
    if [ -n "\$CURRENT_TARGET" ] && [ "\$CURRENT_TARGET" != "\$STAGING_TARGET" ]; then
      LAST_HIST=\$(tail -n 1 "\$HISTORY_FILE" 2>/dev/null || true)
      if [ "\$LAST_HIST" != "\$CURRENT_TARGET" ]; then
        echo "\$CURRENT_TARGET" >> "\$HISTORY_FILE"
      fi
      ln -sfn "\$CURRENT_TARGET" ${VPS_ROOT}/previous
    fi
    
    ln -sfn "\$STAGING_TARGET" ${VPS_ROOT}/current
    echo "✅ Successfully promoted staging (\$(basename \$STAGING_TARGET)) to live!"
EOF
  exit 0
fi

# -------------------------------------------------------------
# MODE 3: DEPLOY TO STAGING
# -------------------------------------------------------------
RELEASE_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REMOTE_RELEASE_DIR="${VPS_ROOT}/releases/${RELEASE_TIMESTAMP}"

if [ "$SKIP_BUILD" = "true" ]; then
  echo "⏩ Skipping build step (--no-build)..."
  if [ ! -d "build/www" ]; then
    echo "❌ Error: build/www/ directory does not exist. Please run 'npm run build:www' first."
    exit 1
  fi
else
  export BASE_PATH="${BASE_PATH:-}"
  echo "🔨 Building site for WWW deployment (BASE_PATH='${BASE_PATH}')..."
  npm run build:www:app
fi

echo "📦 Creating release directory on remote VPS (${REMOTE_RELEASE_DIR})..."
$SSH_CMD "mkdir -p ${REMOTE_RELEASE_DIR} ${VPS_ROOT}/releases"

echo "🚀 Syncing build/www/ to release directory..."
rsync -avz --delete -e "ssh -p ${VPS_PORT}" build/www/ ${VPS_USER}@${VPS_HOST}:${REMOTE_RELEASE_DIR}/

echo "🔗 Updating staging symlink (${VPS_ROOT}/staging -> ${REMOTE_RELEASE_DIR})..."
$SSH_CMD bash -s <<EOF
  set -e
  HISTORY_FILE="${VPS_ROOT}/live_history.txt"
  ln -sfn ${REMOTE_RELEASE_DIR} ${VPS_ROOT}/staging
  
  # Protect active targets & history entries from cleanup
  PROTECTED=()
  [ -d "${VPS_ROOT}/staging" ] && PROTECTED+=("\$(readlink -f ${VPS_ROOT}/staging)")
  [ -d "${VPS_ROOT}/current" ] && PROTECTED+=("\$(readlink -f ${VPS_ROOT}/current)")
  [ -d "${VPS_ROOT}/previous" ] && PROTECTED+=("\$(readlink -f ${VPS_ROOT}/previous)")
  
  if [ -f "\$HISTORY_FILE" ]; then
    while IFS= read -r line || [ -n "\$line" ]; do
      [ -n "\$line" ] && PROTECTED+=("\$line")
    done < "\$HISTORY_FILE"
  fi
  
  # Clean up old releases in releases/, keeping top 5 newest non-protected
  cd ${VPS_ROOT}/releases
  for rel in \$(ls -1dt */ 2>/dev/null | tail -n +6); do
    FULL_PATH="${VPS_ROOT}/releases/\${rel%/}"
    IS_PROTECTED=false
    for prot in "\${PROTECTED[@]}"; do
      if [ "\$FULL_PATH" = "\$prot" ]; then
        IS_PROTECTED=true
        break
      fi
    done
    if [ "\$IS_PROTECTED" = "false" ]; then
      rm -rf "\$FULL_PATH"
    fi
  done
EOF

echo ""
echo "✅ Staging deployment successful!"
echo "🌐 Preview staging build at: https://test.josephus.cbop.faith"
echo "👉 To make this build live, run: npm run deploy:www:promote"
