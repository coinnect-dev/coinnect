# Overnight Report — 2026-03-22

## What was done

### Security fixes (critical)
- [x] **Admin key**: removed hardcoded default `"coinnect-admin-2026"`. Now requires `COINNECT_ADMIN_KEY` env var. Without it, admin endpoints return 503.
- [x] **SQLite WAL mode**: added `PRAGMA journal_mode=WAL` + `busy_timeout=5000` to all 3 DB modules (history, keys, analytics). Safe for 4 uvicorn workers.
- [x] **XSS in /rates/{id}**: all dynamic values now pass through `html.escape()`.
- [x] **XSS in frontend**: added `esc()` helper function. Applied to suggestion names/notes, route labels, provider names, and currency codes in innerHTML.
- [x] **Content-Security-Policy**: added CSP header restricting scripts to self + tailwind CDN + GA4.
- [x] **GA4 GDPR fix**: GA4 no longer loads before consent. Cookie banner now has Accept/Decline buttons. GA4 only loads after explicit Accept.
- [x] **Rate limiting on POST /v1/keys**: max 5 keys per IP per hour.
- [x] **Rate limiting on suggestions/votes**: max 5 suggestions + 20 votes per IP per hour.
- [x] **Health endpoint**: removed `history_db` filesystem path from response.
- [x] **Git remote credentials**: removed Forgejo password from origin URL. Password was NOT in commit history.

### Data fixes
- [x] **WU/MG reverse corridors**: added 10 Western Union reverse corridors (MXN→USD, BRL→USD, etc.) and 8 MoneyGram reverse corridors. Now bidirectional.
- [x] **Rate cache TTL**: all 3 exchange adapters (wise, yellowcard, remittance) now have 5-minute cache TTL instead of infinite cache.

### UX fixes
- [x] **"Disable tracking"**: changed from "No tracking" across all 15 languages to actionable verb form.
- [x] **Cookie banner**: now has Accept/Decline buttons (GDPR compliant).

### Documentation
- [x] **OpenAPI spec**: updated to include all 12 endpoints (was missing 7).
- [x] **Change(b)log**: created first entry at `docs/changelog/2026-03-22.md`.

## What you need to do (before deploy)

1. **Set admin key on ash**:
   ```bash
   # Generate a strong key:
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   # Add to the systemd service or .env file:
   COINNECT_ADMIN_KEY=<generated_key>
   ```

2. **Deploy changes to ash**:
   ```bash
   cd /home/inge/coinnect
   git add -A && git commit -m "security: pre-launch hardening"
   git push origin main
   git push github main
   # On ash: git pull && pip install -e . && systemctl --user restart coinnect
   ```

3. **Set up monitoring** (pick one):
   - UptimeRobot (free): monitor `https://coinnect.bot/v1/health`
   - Or add to Uptime Kuma on ash

4. **Set up backup cron** on ash:
   ```bash
   crontab -e
   # Add: 0 */6 * * * sqlite3 /opt/coinnect/data/history.db ".backup /opt/coinnect/data/history.backup.db"
   ```

5. **Rotate Forgejo password** — the old one was in the git remote URL (now removed, never committed).

## Still pending (not blocking launch)

- API keys stored in plaintext in SQLite (should hash with SHA-256)
- Tailwind CDN → build-time CSS (~300KB → ~15KB)
- Deep-links to providers (Wise, Coinbase, etc.)
- Terms of Service / Privacy Policy pages
- CORS restriction (currently `*`, should restrict to coinnect.bot for non-GET)
- innerHTML in other parts of index.html (most critical ones are now escaped)
- Whitepaper markdown rendering without HTML sanitization

## Six Judges Summary

| Judge | Score | Key insight |
|-------|-------|-------------|
| Technical | 6.5/10 | SQLite bombs defused, cache TTL fixed |
| Economic | 4.5/10 | "5 Pro clients at $100/mo = sustainability" |
| Legal | 7/10 | GA4 consent fixed, needs formal ToS |
| UX | 6.5/10 | Disable tracking text fixed, deep-links pending |
| Security | 5.5/10 | Admin key + XSS + CSP fixed, key hashing pending |
| Launch | 5/10 → 7/10 | Most blockers resolved |

## New ideas logged
- **Change(b)log**: daily AI-written blog at `docs/changelog/`. Need to automate with bot.
- **MTP (Machine Tipping Protocol)**: new project at mtp.bot, work starts tomorrow night.
- **Dual repo strategy**: discuss having a dev repo (Forgejo) and public repo (GitHub) in same org.
