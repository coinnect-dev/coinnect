# Morning Brief — 2026-03-22 → 23

## Tweet (copia y pega)

> I built Coinnect — a free, open-source tool that finds the cheapest way to send money anywhere.
>
> 25+ providers compared in real-time. Fiat, crypto, P2P. No affiliate fees. Ever.
>
> It's like Google Flights, but for remittances.
>
> Try it: https://coinnect.bot

Reply 1:
> Why? A nurse in the Philippines sending $300/month shouldn't lose $18 every time just because she never compared providers.
>
> Coinnect shows every route — ranked by cost. No account needed.

Reply 2:
> For devs & AI agents:
> • REST API, no auth needed
> • MCP server for Claude/AI agents
> • Open data (CC-BY 4.0)
> • MIT license
>
> https://github.com/coinnect-dev/coinnect

## Also post today
- **Show HN**: "Show HN: Coinnect – Free open-source money routing API (25+ providers, MCP)"
- **Reddit**: r/fintech, r/opensource, r/digitalnomad

## Status: everything is live
- Version: 2026.03.22.1
- ash: 4 workers, WAL mode, admin key set, CSP headers
- All WU/MG corridors visible (no more 12-route cap)
- GA4 consent-first (GDPR compliant)
- Google Search Console: verified ✓

## What I did overnight
- Created CODE_OF_CONDUCT.md + SECURITY.md (required for NLnet grant)
- Fixed compound cost calculation (was sum, now product per MRP spec)
- Whitepaper corrections (regulatory language, route count, Yadio)
- Removed $200K salary figure from SUSTAINABILITY.md
- All deployed to ash

## What didn't change (needs your decision)
- x402 badge on homepage (not implemented yet — show "coming soon"?)
- Tailwind CDN → build (saves 300KB, do it this week)
- Terms of Service / Privacy Policy page
- GitHub issues labeled "good first issue" (for contributors)

## Grants: next step
NLnet NGI Zero is the most realistic. Application summary is ready.
Before applying: register with Open Source Collective (fiscal sponsor).
Go to https://opencollective.com/opensource — takes 10 minutes.

## Top insight from the 10-persona review
"The user who needs Coinnect most (migrant worker, 3G, limited English) is the one least served by the current interface."
Priority fix: add delivery method filter (bank, cash pickup, mobile money).
