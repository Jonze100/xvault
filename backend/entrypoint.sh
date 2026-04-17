#!/bin/sh
set -e

# ── Write onchainos CLI config from env vars ────────────────────────────────
# These are set as Railway environment variables (base64-encoded)
ONCHAINOS_DIR="$HOME/.onchainos"
mkdir -p "$ONCHAINOS_DIR"

if [ -n "$ONCHAINOS_SESSION_B64" ]; then
  echo "$ONCHAINOS_SESSION_B64" | base64 -d > "$ONCHAINOS_DIR/session.json"
  echo "[entrypoint] onchainos session.json written"
fi

if [ -n "$ONCHAINOS_WALLETS_B64" ]; then
  echo "$ONCHAINOS_WALLETS_B64" | base64 -d > "$ONCHAINOS_DIR/wallets.json"
  echo "[entrypoint] onchainos wallets.json written"
fi

if [ -n "$ONCHAINOS_MACHINE_ID_B64" ]; then
  echo "$ONCHAINOS_MACHINE_ID_B64" | base64 -d > "$ONCHAINOS_DIR/machine-identity"
  chmod 600 "$ONCHAINOS_DIR/machine-identity"
  echo "[entrypoint] onchainos machine-identity written"
fi

# Verify onchainos is installed and authenticated
if command -v onchainos >/dev/null 2>&1; then
  echo "[entrypoint] onchainos binary found: $(onchainos --version 2>/dev/null || echo 'unknown')"
  onchainos wallet status 2>/dev/null | head -5 || echo "[entrypoint] onchainos wallet status check failed"
else
  echo "[entrypoint] WARNING: onchainos binary not found at expected path"
  # Try to install it
  curl -fsSL https://raw.githubusercontent.com/nicefellow1234/onchainos-skills/main/install.sh | bash || true
fi

# ── Start the backend ───────────────────────────────────────────────────────
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
