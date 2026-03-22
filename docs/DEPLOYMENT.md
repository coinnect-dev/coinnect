# Coinnect — Deployment Guide

## Requirements

- Python 3.11+
- Linux (systemd)
- Port 8100 (or any, behind a reverse proxy)
- Outbound HTTPS to exchange APIs

```bash
git clone https://github.com/coinnect-dev/coinnect.git
cd coinnect
pip install -e .
mkdir -p data
```

---

## systemd service

Create `/etc/systemd/system/coinnect.service`:

```ini
[Unit]
Description=Coinnect API
After=network.target

[Service]
Type=exec
User=coinnect
WorkingDirectory=/opt/coinnect
EnvironmentFile=/opt/coinnect/.env
ExecStart=/opt/coinnect/.venv/bin/uvicorn coinnect.main:app \
    --host 0.0.0.0 \
    --port 8100 \
    --workers 4 \
    --access-log \
    --log-level info
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=coinnect

[Install]
WantedBy=multi-user.target
```

> **`--workers 4`** runs 4 independent processes. Recommended: 2× CPU cores.
> SQLite is safe with multiple workers — each process opens its own connection.
> Background rate refresh runs in each worker (redundant, harmless — each captures its own snapshot).
> If you need a single canonical refresh, set `--workers 1` and use an external cron for snapshots.

### `.env` file

```
COINNECT_ADMIN_KEY=your-secret-admin-key
WISE_API_KEY=your-wise-api-key
YELLOWCARD_API_KEY=your-yellowcard-api-key
```

### Enable and start

```bash
systemctl daemon-reload
systemctl enable --now coinnect
journalctl -u coinnect -f
```

---

## Caddy reverse proxy (recommended)

```caddy
coinnect.bot {
    reverse_proxy localhost:8100
    encode gzip
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        -Server
    }
}
```

---

## Cloudflare setup

### DNS

| Type | Name | Target | Proxy |
|------|------|--------|-------|
| A | @ | your-server-ip | ✓ (orange cloud) |
| CNAME | www | coinnect.bot | ✓ |

### Cache Rules (Cloudflare dashboard → Rules → Cache Rules)

**Rule 1: Cache `/v1/quote` for 60 seconds**

- Expression: `(http.request.uri.path eq "/v1/quote")`
- Cache eligibility: Eligible for cache
- Edge TTL: 60 seconds (ignore origin Cache-Control)
- Browser TTL: 30 seconds
- Cache key: Include query string (default)

This means the first request in 60s hits your server; all subsequent identical queries hit Cloudflare edge. For anonymous users doing the same USD→MXN search, 99% of traffic is served from cache — effectively unlimited scale at zero server cost.

**Rule 2: Cache static assets for 7 days**

- Expression: `(http.request.uri.path matches "^/static/")`
- Edge TTL: 7 days
- Browser TTL: 1 day

**Rule 3: Bypass cache for admin and API keys**

- Expression: `(http.request.uri.path matches "^/admin/") or (http.request.headers["x-api-key"] ne "")`
- Cache eligibility: Bypass cache

### Rate limiting (Cloudflare → Security → Rate Limiting)

As a free-tier safety net (in addition to Coinnect's in-process limits):

- Path: `/v1/*`
- Threshold: 200 requests / 10 minutes per IP
- Action: Block for 1 hour

---

## Scaling beyond a single server

The quote engine is stateless — it reads from in-memory exchange caches. Horizontal scaling is trivial:

1. Run multiple `coinnect` instances behind a load balancer.
2. Move SQLite databases to [Turso](https://turso.tech) (libSQL over HTTP) — drop-in replacement.
3. Cache `/v1/quote` at Cloudflare edge (60s TTL already covers burst traffic).

At 10,000 daily users, a single 4-core VPS with Cloudflare caching handles load comfortably.

---

## Cloudflare Tunnel (home / cabin hosting)

If your server doesn't have a static IP (home connection, cabin, mobile):

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Authenticate
cloudflared tunnel login

# Create a tunnel
cloudflared tunnel create coinnect

# Route traffic
cloudflared tunnel route dns coinnect coinnect.bot

# Run (or add to systemd)
cloudflared tunnel run --url http://localhost:8100 coinnect
```

With a Cloudflare Tunnel, your server gets a persistent domain even with a dynamic IP. Works from a home server, a cabin on cellular, or a GMKtec mini PC.

---

## Database locations

| DB | Default path | Purpose |
|----|-------------|---------|
| `data/history.db` | Repo root `/data/` | Rate snapshots, provider history |
| `data/history.db` (same) | — | API keys, analytics, suggestions |

All three logical schemas (history, keys, analytics) share one file. Back up with:

```bash
sqlite3 data/history.db ".backup data/history.backup.db"
```

---

## Health check

```bash
curl https://coinnect.bot/v1/health
```

Expected response:
```json
{"ok": true, "status": "live", "version": "2026.03.22.x", ...}
```
