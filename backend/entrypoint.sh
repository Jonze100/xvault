#!/bin/sh
set -e

# ── Write onchainos CLI config from env vars ────────────────────────────────
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

# Also write to XDG config dir
XDG_ONCHAINOS="$HOME/.config/onchainos"
mkdir -p "$XDG_ONCHAINOS"
[ -f "$ONCHAINOS_DIR/session.json" ] && cp "$ONCHAINOS_DIR/session.json" "$XDG_ONCHAINOS/"
[ -f "$ONCHAINOS_DIR/wallets.json" ] && cp "$ONCHAINOS_DIR/wallets.json" "$XDG_ONCHAINOS/"
[ -f "$ONCHAINOS_DIR/machine-identity" ] && cp "$ONCHAINOS_DIR/machine-identity" "$XDG_ONCHAINOS/" && chmod 600 "$XDG_ONCHAINOS/machine-identity"
[ -f "$ONCHAINOS_DIR/chain_cache.json" ] && cp "$ONCHAINOS_DIR/chain_cache.json" "$XDG_ONCHAINOS/"
echo '{}' > "$XDG_ONCHAINOS/cache.json"

# ── Authenticate onchainos via API Key (AK login) ──────────────────────────
# The TEE session from macOS doesn't transfer to Linux containers.
# Use OKX API keys to authenticate directly on this machine.
if command -v onchainos >/dev/null 2>&1; then
  echo "[entrypoint] onchainos binary found: $(onchainos --version 2>/dev/null || echo 'unknown')"

  # Check if already logged in
  LOGGED_IN=$(onchainos wallet status 2>&1 | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['data']['loggedIn'])" 2>/dev/null || echo "False")

  if [ "$LOGGED_IN" = "True" ]; then
    echo "[entrypoint] onchainos already logged in"
  else
    echo "[entrypoint] onchainos not logged in — attempting AK (API Key) login..."
    # AK login: omit email, uses OKX_API_KEY / OKX_SECRET_KEY / OKX_PASSPHRASE env vars
    # or the apiKey in session.json
    if [ -n "$OKX_API_KEY" ] && [ -n "$OKX_SECRET_KEY" ] && [ -n "$OKX_PASSPHRASE" ]; then
      # Write API key into session.json so onchainos can use it
      python3 -c "
import json
try:
    with open('$ONCHAINOS_DIR/session.json') as f:
        d = json.load(f)
except:
    d = {}
d['apiKey'] = '$OKX_API_KEY'
d['secretKey'] = '$OKX_SECRET_KEY'
d['passphrase'] = '$OKX_PASSPHRASE'
d['projectId'] = '${OKX_PROJECT_ID:-}'
with open('$ONCHAINOS_DIR/session.json', 'w') as f:
    json.dump(d, f, indent=2)
# Also copy to XDG
import shutil
shutil.copy('$ONCHAINOS_DIR/session.json', '$XDG_ONCHAINOS/session.json')
" 2>/dev/null && echo "[entrypoint] API keys injected into session.json"

      # Try AK login (no email = API key mode)
      onchainos wallet login --force 2>&1 | head -5 || echo "[entrypoint] AK login attempt completed"
    fi

    # Re-check login status
    onchainos wallet status 2>&1 | head -15 || echo "[entrypoint] wallet status check failed"
  fi
else
  echo "[entrypoint] WARNING: onchainos binary not found"
  curl -fsSL https://raw.githubusercontent.com/nicefellow1234/onchainos-skills/main/install.sh | bash || true
fi

# ── Start the backend ───────────────────────────────────────────────────────
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
