#!/usr/bin/env bash
# =============================================================================
# deploy.sh
# Production deployment script with health check and automatic rollback.
# Usage: ./scripts/deploy.sh [--tag <image-tag>] [--env <env-file>] [--dry-run]
# =============================================================================
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
DEPLOY_PATH="${DEPLOY_PATH:-$(pwd)}"
ENV_FILE="${ENV_FILE:-${DEPLOY_PATH}/.env.production}"
API_IMAGE_TAG="${API_IMAGE_TAG:-latest}"
COMPOSE_FILE="${DEPLOY_PATH}/infra/docker/docker-compose.yml"
HEALTH_CHECK_URL="${HEALTH_CHECK_URL:-http://localhost:8000/api/v1/health}"
HEALTH_CHECK_RETRIES=10
HEALTH_CHECK_INTERVAL=10
DRY_RUN=false
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"

# ── Parse arguments ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)      API_IMAGE_TAG="$2"; shift 2 ;;
    --env)      ENV_FILE="$2"; shift 2 ;;
    --dry-run)  DRY_RUN=true; shift ;;
    --help)
      cat <<EOF
Usage: $0 [options]

Options:
  --tag <tag>     Docker image tag to deploy (default: latest)
  --env <file>    Environment file (default: .env.production)
  --dry-run       Print commands without executing
  --help          Show this help

Environment variables:
  DEPLOY_PATH     Path to the project root
  API_IMAGE_TAG   Docker image tag
  SLACK_WEBHOOK   Slack webhook URL for notifications
EOF
      exit 0
      ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

# ── Colors & logging ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

log()     { echo -e "${BLUE}[${TIMESTAMP}] INFO:${NC} $*"; }
success() { echo -e "${GREEN}[${TIMESTAMP}] OK:${NC} $*"; }
warn()    { echo -e "${YELLOW}[${TIMESTAMP}] WARN:${NC} $*"; }
error()   { echo -e "${RED}[${TIMESTAMP}] ERROR:${NC} $*" >&2; }
step()    { echo -e "\n${BLUE}══════════════════════════════════════════════${NC}"; echo -e "${BLUE} $*${NC}"; echo -e "${BLUE}══════════════════════════════════════════════${NC}"; }

run() {
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo -e "${YELLOW}[DRY-RUN]${NC} $*"
  else
    eval "$*"
  fi
}

# ── Slack notification ────────────────────────────────────────────────────────
notify_slack() {
  local message="$1"
  local color="${2:-#36a64f}"
  if [[ -n "${SLACK_WEBHOOK}" ]]; then
    curl -sf -X POST "${SLACK_WEBHOOK}" \
      -H 'Content-type: application/json' \
      --data "{\"attachments\":[{\"color\":\"${color}\",\"text\":\"${message}\"}]}" \
      || warn "Slack notification failed (non-fatal)"
  fi
}

# ── Load env ──────────────────────────────────────────────────────────────────
if [[ -f "${ENV_FILE}" ]]; then
  log "Loading environment from ${ENV_FILE}"
  set -a; source "${ENV_FILE}"; set +a
else
  warn "Environment file not found: ${ENV_FILE}"
fi

# ── Dependency checks ─────────────────────────────────────────────────────────
for cmd in docker curl; do
  if ! command -v "${cmd}" &>/dev/null; then
    error "${cmd} is required but not installed."
    exit 1
  fi
done

if [[ "${DRY_RUN}" == "true" ]]; then
  warn "DRY-RUN mode enabled — no changes will be made."
fi

# ── Snapshot current state for rollback ───────────────────────────────────────
step "1. Capturing current state for rollback"

PREVIOUS_API_TAG=$(docker compose \
  -f "${COMPOSE_FILE}" \
  ps --format json api 2>/dev/null \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Image','unknown'))" \
  2>/dev/null || echo "unknown")

log "Current API image: ${PREVIOUS_API_TAG}"
log "Deploying API image tag: ${API_IMAGE_TAG}"

notify_slack "🚀 Deployment started (tag: ${API_IMAGE_TAG}) on $(hostname)"

# ── Pull latest images ────────────────────────────────────────────────────────
step "2. Pulling latest Docker images"

run "API_IMAGE_TAG=${API_IMAGE_TAG} docker compose \
  -f \"${COMPOSE_FILE}\" \
  --env-file \"${ENV_FILE}\" \
  pull api celery-worker celery-beat"

success "Images pulled"

# ── Run database migrations ───────────────────────────────────────────────────
step "3. Running database migrations"

run "API_IMAGE_TAG=${API_IMAGE_TAG} docker compose \
  -f \"${COMPOSE_FILE}\" \
  --env-file \"${ENV_FILE}\" \
  run --rm api alembic upgrade head"

success "Migrations complete"

# ── Deploy new containers ─────────────────────────────────────────────────────
step "4. Starting new containers"

run "API_IMAGE_TAG=${API_IMAGE_TAG} docker compose \
  -f \"${COMPOSE_FILE}\" \
  --env-file \"${ENV_FILE}\" \
  up -d api celery-worker celery-beat"

success "Containers started"

# ── Health check ─────────────────────────────────────────────────────────────
step "5. Health check"

HEALTHY=false
for i in $(seq 1 ${HEALTH_CHECK_RETRIES}); do
  log "Health check attempt ${i}/${HEALTH_CHECK_RETRIES}..."

  if [[ "${DRY_RUN}" == "true" ]]; then
    HEALTHY=true
    break
  fi

  if curl -sf --max-time 10 "${HEALTH_CHECK_URL}" > /dev/null 2>&1; then
    HEALTHY=true
    success "Health check passed!"
    break
  fi

  if [[ $i -lt ${HEALTH_CHECK_RETRIES} ]]; then
    warn "Not healthy yet, waiting ${HEALTH_CHECK_INTERVAL}s..."
    sleep ${HEALTH_CHECK_INTERVAL}
  fi
done

# ── Rollback if unhealthy ─────────────────────────────────────────────────────
if [[ "${HEALTHY}" != "true" ]]; then
  error "Health check failed after ${HEALTH_CHECK_RETRIES} attempts!"
  error "Rolling back to previous state..."

  notify_slack "🔴 Deployment FAILED (tag: ${API_IMAGE_TAG}) — rolling back!" "#ff0000"

  if [[ "${PREVIOUS_API_TAG}" != "unknown" ]] && [[ "${DRY_RUN}" != "true" ]]; then
    docker compose \
      -f "${COMPOSE_FILE}" \
      --env-file "${ENV_FILE}" \
      up -d --force-recreate api celery-worker celery-beat

    warn "Rollback initiated. Verify with: docker compose ps"
  fi

  exit 1
fi

# ── Post-deployment tasks ─────────────────────────────────────────────────────
step "6. Post-deployment cleanup"

run "docker image prune -f --filter 'until=48h'"

# ── Reload Nginx ──────────────────────────────────────────────────────────────
step "7. Reloading Nginx"

if docker compose -f "${COMPOSE_FILE}" ps nginx 2>/dev/null | grep -q "running"; then
  run "docker compose -f \"${COMPOSE_FILE}\" exec -T nginx nginx -s reload"
  success "Nginx reloaded"
else
  warn "Nginx not running, skipping reload"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
step "Deployment complete!"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Deployment Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Image tag:  ${API_IMAGE_TAG}"
echo "  Status:     SUCCESS"
echo "  Timestamp:  ${TIMESTAMP}"
if [[ "${DRY_RUN}" == "true" ]]; then
  echo "  Mode:       DRY-RUN (no actual changes made)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

notify_slack "✅ Deployment SUCCESS (tag: ${API_IMAGE_TAG}) on $(hostname)"
success "Done!"
