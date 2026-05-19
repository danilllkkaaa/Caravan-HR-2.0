#!/usr/bin/env bash
# =============================================================================
# backup-db.sh
# Creates a PostgreSQL database backup and uploads it to S3 / MinIO.
# Usage: ./scripts/backup-db.sh [--env <env-file>]
# Schedule via cron: 0 2 * * * /path/to/scripts/backup-db.sh >> /var/log/portal-backup.log 2>&1
# =============================================================================
set -euo pipefail

# ── Config (override via environment or --env flag) ───────────────────────────
ENV_FILE="${ENV_FILE:-.env.production}"
BACKUP_DIR="${BACKUP_DIR:-/tmp/portal-backups}"
RETAIN_LOCAL_DAYS="${RETAIN_LOCAL_DAYS:-3}"
RETAIN_S3_DAYS="${RETAIN_S3_DAYS:-30}"

# PostgreSQL
PG_HOST="${POSTGRES_HOST:-localhost}"
PG_PORT="${POSTGRES_PORT:-5432}"
PG_DB="${POSTGRES_DB:-portal}"
PG_USER="${POSTGRES_USER:-portal}"
PG_PASSWORD="${POSTGRES_PASSWORD:-}"

# S3 / MinIO
S3_BUCKET="${BACKUP_S3_BUCKET:-portal-backups}"
S3_PREFIX="${BACKUP_S3_PREFIX:-postgres}"
S3_ENDPOINT="${BACKUP_S3_ENDPOINT:-}"  # Empty = AWS S3; set for MinIO

# ── Parse arguments ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env) ENV_FILE="$2"; shift 2 ;;
    --help)
      echo "Usage: $0 [--env <env-file>]"
      exit 0
      ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

# ── Load environment file ─────────────────────────────────────────────────────
if [[ -f "${ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  set -a; source "${ENV_FILE}"; set +a
fi

# ── Colors & logging ──────────────────────────────────────────────────────────
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DATESTAMP=$(date '+%Y%m%d_%H%M%S')

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

log()     { echo -e "${BLUE}[${TIMESTAMP}]${NC} $*"; }
success() { echo -e "${GREEN}[${TIMESTAMP}] OK:${NC} $*"; }
warn()    { echo -e "${YELLOW}[${TIMESTAMP}] WARN:${NC} $*"; }
error()   { echo -e "${RED}[${TIMESTAMP}] ERROR:${NC} $*" >&2; }

# ── Dependency checks ─────────────────────────────────────────────────────────
for cmd in pg_dump gzip aws; do
  if ! command -v "${cmd}" &>/dev/null; then
    error "${cmd} is required but not installed."
    exit 1
  fi
done

# ── Setup ─────────────────────────────────────────────────────────────────────
mkdir -p "${BACKUP_DIR}"

BACKUP_FILENAME="${PG_DB}_${DATESTAMP}.sql.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"
S3_KEY="${S3_PREFIX}/${BACKUP_FILENAME}"

# ── Create backup ─────────────────────────────────────────────────────────────
log "Starting backup of database '${PG_DB}' on ${PG_HOST}:${PG_PORT}"

export PGPASSWORD="${PG_PASSWORD}"

pg_dump \
  --host="${PG_HOST}" \
  --port="${PG_PORT}" \
  --username="${PG_USER}" \
  --dbname="${PG_DB}" \
  --format=plain \
  --no-owner \
  --no-acl \
  --verbose \
  2>/tmp/pg_dump_verbose.log \
  | gzip -9 > "${BACKUP_PATH}"

unset PGPASSWORD

BACKUP_SIZE=$(du -sh "${BACKUP_PATH}" | cut -f1)
success "Backup created: ${BACKUP_PATH} (${BACKUP_SIZE})"

# ── Upload to S3 / MinIO ──────────────────────────────────────────────────────
log "Uploading to s3://${S3_BUCKET}/${S3_KEY}..."

AWS_ARGS=(
  "s3" "cp"
  "${BACKUP_PATH}"
  "s3://${S3_BUCKET}/${S3_KEY}"
  "--storage-class" "STANDARD_IA"
)

# MinIO / custom endpoint
if [[ -n "${S3_ENDPOINT}" ]]; then
  AWS_ARGS+=("--endpoint-url" "${S3_ENDPOINT}")
fi

if aws "${AWS_ARGS[@]}" 2>&1; then
  success "Uploaded to s3://${S3_BUCKET}/${S3_KEY}"
else
  error "S3 upload failed! Local backup preserved at ${BACKUP_PATH}"
  exit 1
fi

# ── Set lifecycle / tag for retention ─────────────────────────────────────────
TAG_ARGS=(
  "s3api" "put-object-tagging"
  "--bucket" "${S3_BUCKET}"
  "--key" "${S3_KEY}"
  "--tagging" "{\"TagSet\":[{\"Key\":\"RetainDays\",\"Value\":\"${RETAIN_S3_DAYS}\"}]}"
)

if [[ -n "${S3_ENDPOINT}" ]]; then
  TAG_ARGS+=("--endpoint-url" "${S3_ENDPOINT}")
fi

aws "${TAG_ARGS[@]}" || warn "Failed to tag S3 object (non-fatal)"

# ── Cleanup old local backups ─────────────────────────────────────────────────
log "Cleaning up local backups older than ${RETAIN_LOCAL_DAYS} days..."
find "${BACKUP_DIR}" -name "${PG_DB}_*.sql.gz" -mtime "+${RETAIN_LOCAL_DAYS}" -delete
success "Local cleanup done"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Backup Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Database:  ${PG_DB}"
echo "  File:      ${BACKUP_FILENAME}"
echo "  Size:      ${BACKUP_SIZE}"
echo "  S3 path:   s3://${S3_BUCKET}/${S3_KEY}"
echo "  Timestamp: ${TIMESTAMP}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
success "Backup completed successfully!"
