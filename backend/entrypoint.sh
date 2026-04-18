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

if [ -n "$ONCHAINOS_CHAIN_CACHE_B64" ]; then
  echo "$ONCHAINOS_CHAIN_CACHE_B64" | base64 -d > "$ONCHAINOS_DIR/chain_cache.json"
  echo "[entrypoint] onchainos chain_cache.json written"
fi

# Initialize empty cache
echo '{}' > "$ONCHAINOS_DIR/cache.json"

# Also write to XDG config dir in case onchainos looks there
XDG_ONCHAINOS="$HOME/.config/onchainos"
mkdir -p "$XDG_ONCHAINOS"
[ -f "$ONCHAINOS_DIR/session.json" ] && cp "$ONCHAINOS_DIR/session.json" "$XDG_ONCHAINOS/"
[ -f "$ONCHAINOS_DIR/wallets.json" ] && cp "$ONCHAINOS_DIR/wallets.json" "$XDG_ONCHAINOS/"
[ -f "$ONCHAINOS_DIR/machine-identity" ] && cp "$ONCHAINOS_DIR/machine-identity" "$XDG_ONCHAINOS/" && chmod 600 "$XDG_ONCHAINOS/machine-identity"
[ -f "$ONCHAINOS_DIR/chain_cache.json" ] && cp "$ONCHAINOS_DIR/chain_cache.json" "$XDG_ONCHAINOS/"
echo '{}' > "$XDG_ONCHAINOS/cache.json"
echo "[entrypoint] onchainos config also copied to $XDG_ONCHAINOS"

# Debug: show which account is active
echo "[entrypoint] wallets.json selectedAccountId: $(python3 -c "import json; d=json.load(open('$ONCHAINOS_DIR/wallets.json')); print(d.get('selectedAccountId','UNKNOWN'))" 2>/dev/null || echo 'parse failed')"
echo "[entrypoint] session.json accountId: $(python3 -c "import json; d=json.load(open('$ONCHAINOS_DIR/session.json')); print(d.get('accountId', d.get('account_id','UNKNOWN')))" 2>/dev/null || echo 'parse failed')"
echo "[entrypoint] session.json keys: $(python3 -c "import json; d=json.load(open('$ONCHAINOS_DIR/session.json')); print(list(d.keys()))" 2>/dev/null || echo 'parse failed')"

# Verify onchainos is installed and authenticated
if command -v onchainos >/dev/null 2>&1; then
  echo "[entrypoint] onchainos binary found: $(onchainos --version 2>/dev/null || echo 'unknown')"
  echo "[entrypoint] onchainos wallet status:"
  onchainos wallet status 2>&1 | head -10 || echo "[entrypoint] onchainos wallet status check failed"
  echo "[entrypoint] onchainos config dir contents:"
  ls -la "$ONCHAINOS_DIR/" 2>/dev/null || true
  ls -la "$XDG_ONCHAINOS/" 2>/dev/null || true
  # Try to select the correct wallet
  onchainos wallet select --account-id "7b76a28d-3007-410b-b8ee-a1632c7035d8" 2>&1 || echo "[entrypoint] wallet select failed"
else
  echo "[entrypoint] WARNING: onchainos binary not found at expected path"
  # Try to install it
  curl -fsSL https://raw.githubusercontent.com/nicefellow1234/onchainos-skills/main/install.sh | bash || true
fi

# ── Start the backend ───────────────────────────────────────────────────────
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
