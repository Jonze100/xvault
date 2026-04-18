#!/bin/sh
set -e

# ── Write onchainos CLI config from env vars ────────────────────────────────
# Session created via `onchainos wallet login` on Railway SSH, then exported
# as base64 env var. This is a Linux-native TEE session — no cross-platform issues.
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

if [ -n "$ONCHAINOS_CHAIN_CACHE_B64" ]; then
  echo "$ONCHAINOS_CHAIN_CACHE_B64" | base64 -d > "$ONCHAINOS_DIR/chain_cache.json"
  echo "[entrypoint] onchainos chain_cache.json written"
fi

echo '{}' > "$ONCHAINOS_DIR/cache.json"

# Also write to XDG config dir in case onchainos looks there
XDG_ONCHAINOS="$HOME/.config/onchainos"
mkdir -p "$XDG_ONCHAINOS"
[ -f "$ONCHAINOS_DIR/session.json" ] && cp "$ONCHAINOS_DIR/session.json" "$XDG_ONCHAINOS/"
[ -f "$ONCHAINOS_DIR/wallets.json" ] && cp "$ONCHAINOS_DIR/wallets.json" "$XDG_ONCHAINOS/"
[ -f "$ONCHAINOS_DIR/machine-identity" ] && cp "$ONCHAINOS_DIR/machine-identity" "$XDG_ONCHAINOS/" && chmod 600 "$XDG_ONCHAINOS/machine-identity"
[ -f "$ONCHAINOS_DIR/chain_cache.json" ] && cp "$ONCHAINOS_DIR/chain_cache.json" "$XDG_ONCHAINOS/"
echo '{}' > "$XDG_ONCHAINOS/cache.json"

# ── Verify onchainos auth ──────────────────────────────────────────────────
if command -v onchainos >/dev/null 2>&1; then
  echo "[entrypoint] onchainos $(onchainos --version 2>/dev/null || echo 'unknown')"
  # Show wallet status — should show loggedIn:true with email account 7b76a28d
  onchainos wallet status 2>&1 | head -15 || echo "[entrypoint] wallet status failed"
else
  echo "[entrypoint] WARNING: onchainos binary not found"
  curl -fsSL https://raw.githubusercontent.com/nicefellow1234/onchainos-skills/main/install.sh | bash || true
fi

# ── Start the backend ───────────────────────────────────────────────────────
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
