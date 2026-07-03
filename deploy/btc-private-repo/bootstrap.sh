#!/usr/bin/env bash
# Assemble the private btc-tracker repo from this Stock-Screener checkout.
# Usage: bash deploy/btc-private-repo/bootstrap.sh /path/to/btc-tracker-clone
set -euo pipefail

SRC="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="${1:?usage: bootstrap.sh /path/to/btc-tracker-clone}"

mkdir -p "$DEST/scripts" "$DEST/templates" "$DEST/tests" "$DEST/data" \
    "$DEST/.github/workflows"

cp -r "$SRC/btc_tracker" "$DEST/"
rm -rf "$DEST/btc_tracker/__pycache__"
cp "$SRC/scripts/btc_tracker.py" "$DEST/scripts/"
cp "$SRC/templates/btc_dashboard.html" "$DEST/templates/"
cp "$SRC/tests/test_btc_costbasis.py" "$DEST/tests/"
cp "$SRC/deploy/btc-private-repo/README.md" "$DEST/README.md"
cp "$SRC/deploy/btc-private-repo/update.yml" "$DEST/.github/workflows/update.yml"
touch "$DEST/data/.gitkeep"

cat > "$DEST/requirements.txt" <<'EOF'
jinja2>=3.1.0
requests>=2.31.0
PyJWT>=2.8.0
cryptography>=42.0.0
pytest>=7.0.0
EOF

cat > "$DEST/.gitignore" <<'EOF'
.env
*.pyc
__pycache__/
private/
# API-fetched cache (rebuilt each run). Manual entries ARE committed.
data/btc_transactions.json
EOF

cat > "$DEST/.env.example" <<'EOF'
KRAKEN_API_KEY=
KRAKEN_API_SECRET=
# Either point at the downloaded key file...
COINBASE_KEY_FILE=~/.keys/cdp_api_key.json
# ...or set the two fields directly:
# COINBASE_API_KEY_NAME=organizations/xxx/apiKeys/yyy
# COINBASE_API_PRIVATE_KEY=-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----\n
PHANTOM_BTC_ADDRESSES=
BTC_DASHBOARD_URL=https://ocovjbvrtbxptqtucyqw.supabase.co/functions/v1/btc-dashboard
BTC_PUBLISH_TOKEN=
EOF

echo "Assembled private repo content in $DEST"
