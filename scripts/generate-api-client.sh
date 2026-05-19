#!/usr/bin/env bash
# =============================================================================
# generate-api-client.sh
# Generates TypeScript API client from FastAPI OpenAPI schema.
# Usage: ./scripts/generate-api-client.sh [--url <openapi-url>] [--output <dir>]
# =============================================================================
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
OPENAPI_URL="${OPENAPI_URL:-http://localhost:8000/openapi.json}"
OUTPUT_DIR="${OUTPUT_DIR:-packages/api-client/src}"
TEMP_SCHEMA="/tmp/openapi-schema-$$.json"
PACKAGE_NAME="@corp-portal/api-client"

# ── Parse arguments ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)   OPENAPI_URL="$2"; shift 2 ;;
    --output) OUTPUT_DIR="$2"; shift 2 ;;
    --help)
      echo "Usage: $0 [--url <openapi-url>] [--output <output-dir>]"
      echo ""
      echo "  --url     OpenAPI schema URL (default: ${OPENAPI_URL})"
      echo "  --output  Output directory (default: ${OUTPUT_DIR})"
      exit 0
      ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ── Dependency checks ─────────────────────────────────────────────────────────
info "Checking dependencies..."

if ! command -v curl &>/dev/null; then
  error "curl is required but not installed."
  exit 1
fi

if ! command -v node &>/dev/null; then
  error "node is required but not installed."
  exit 1
fi

if ! command -v pnpm &>/dev/null; then
  warn "pnpm not found, falling back to npx"
  CODEGEN_CMD="npx --yes openapi-typescript-codegen"
else
  # Install openapi-typescript-codegen if not present
  if ! pnpm list openapi-typescript-codegen --global &>/dev/null 2>&1; then
    info "Installing openapi-typescript-codegen..."
    pnpm install -g openapi-typescript-codegen
  fi
  CODEGEN_CMD="openapi-typescript-codegen"
fi

# ── Fetch OpenAPI schema ──────────────────────────────────────────────────────
info "Fetching OpenAPI schema from: ${OPENAPI_URL}"

if ! curl -sf --max-time 30 "${OPENAPI_URL}" -o "${TEMP_SCHEMA}"; then
  error "Failed to fetch OpenAPI schema from ${OPENAPI_URL}"
  error "Make sure the API server is running."
  exit 1
fi

# Validate it's valid JSON
if ! python3 -m json.tool "${TEMP_SCHEMA}" > /dev/null 2>&1; then
  error "Downloaded file is not valid JSON"
  rm -f "${TEMP_SCHEMA}"
  exit 1
fi

API_TITLE=$(python3 -c "import json,sys; d=json.load(open('${TEMP_SCHEMA}')); print(d.get('info',{}).get('title','Unknown'))" 2>/dev/null || echo "Unknown")
API_VERSION=$(python3 -c "import json,sys; d=json.load(open('${TEMP_SCHEMA}')); print(d.get('info',{}).get('version','0.0.0'))" 2>/dev/null || echo "0.0.0")

success "Schema fetched: ${API_TITLE} v${API_VERSION}"

# ── Generate TypeScript client ────────────────────────────────────────────────
info "Generating TypeScript client to: ${OUTPUT_DIR}"

mkdir -p "${OUTPUT_DIR}"

${CODEGEN_CMD} \
  --input "${TEMP_SCHEMA}" \
  --output "${OUTPUT_DIR}" \
  --client axios \
  --name "PortalApiClient" \
  --useOptions \
  --useUnionTypes

# ── Cleanup ───────────────────────────────────────────────────────────────────
rm -f "${TEMP_SCHEMA}"

# ── Post-generation fixes ─────────────────────────────────────────────────────
# Add package.json if missing
PACKAGE_JSON="${OUTPUT_DIR}/../package.json"
if [[ ! -f "${PACKAGE_JSON}" ]]; then
  info "Creating package.json for ${PACKAGE_NAME}..."
  cat > "${PACKAGE_JSON}" <<EOF
{
  "name": "${PACKAGE_NAME}",
  "version": "${API_VERSION}",
  "private": true,
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "exports": {
    ".": "./src/index.ts"
  },
  "dependencies": {
    "axios": "^1.7.0"
  }
}
EOF
fi

success "API client generated successfully!"
echo ""
echo "Output: ${OUTPUT_DIR}"
echo "Usage:  import { PortalApiClient } from '${PACKAGE_NAME}';"
echo ""
info "To update the client, run: ./scripts/generate-api-client.sh"
