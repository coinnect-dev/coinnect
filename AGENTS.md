---
type: agents-card
name: "Coinnect · reglas para agentes"
slug: coinnect-agents
owner: miguel
status: live
tags: [agents]
last_updated: 2026-11-02
related: [coinnect]
---

<!-- KOA-MANUAL -->
# AGENTS.md — Coinnect

> Cross-agente. **Nota:** este repo es independiente — no depende de ninguna infraestructura interna para contribuir. Si corrés tu propio orquestador de agentes, llevá tu propio ledger de actividad vía las env vars que tu tooling soporte.

## Qué es

Exchange router multi-corredor: stable → MXN/local con rutas rankeadas. Web `coinnect.bot`. API `/v1/quote?from=USD&to=MXN&amount=500`. ~80 adapters activos (Kraken, Binance, Coinbase, Bitso CCXT + Wise + Yellow Card + WU + MoneyGram + más).

## Stack

- FastAPI + CCXT + Wise SDK.
- SQLite `data/history.db`.
- Background refresh cada ~3 min en su propio hilo y event loop (`_Refresher` en `main.py`).
- **Una sola worker de uvicorn** (`--workers 1`): cada proceso corre su propio refresher, así que más workers multiplican llamadas upstream y filas de snapshots, y parten los rate limits en memoria.
- MCP server: `python -m coinnect.mcp_server` (tools `coinnect_quote`, `coinnect_corridors`, `coinnect_explain_route`).

## Build & Deploy

```bash
cd coinnect
pip install -e .[dev]
pytest
# deploy (adapt to your own host/user)
rsync -avz . <user>@<prod-host>:/path/to/coinnect/
ssh <user>@<prod-host> "systemctl --user restart coinnect"
curl -fsS https://coinnect.bot/v1/quote?from=USD\&to=MXN\&amount=500 | head
```

Servicio prod corre en puerto 8100 (`coinnect.service`, systemd user unit).

## Reglas

- Cero credenciales hardcoded. Wise API key vía env. Exchange APIs vía CCXT + env keys.
- Adapters son plugins en `coinnect/adapters/*.py`. Agregar nuevo = nueva clase + registry.
- Ratings en `data/history.db` informan ranking. NO eliminar histórico: `compact_history()` deja una fila por hora tras 7 días y saca la tabla viva a los 30, pero archiva todo lo que quita en `data/archive/*.jsonl.gz`.
- Rutas: solo pasan por `ROUTING_HUBS` (fiat + USDT/USDC/DAI/BTC/ETH); los altcoins sirven como origen o destino. Ampliar hubs sube el CPU mucho.
- `build_public_quote` es CPU-bound: nunca en el event loop.
- IP del cliente para rate limits: siempre `coinnect.net.client_ip` (el origin se alcanza sin Cloudflare; `CF-Connecting-IP` solo vale si el peer es Cloudflare). Actualiza sus CIDR si Cloudflare los cambia.
- API keys: solo SHA-256 en reposo.
- Traducciones: `static/i18n/<lang>.js` se cargan bajo demanda; inglés va en `i18n.js`. Sube `_I18N_V` al cambiarlas.
- Pentest 2026-04-07: XSS reflected/stored fixed, HSTS al origin OK. Cloudflare HSTS edge sigue 0 (toggle pendiente Miguel).

## Pendientes

- Cloudflare HSTS edge.
- Cartera Nigeria (60+ rails, sesión 2026-03-28).
- Webhook secrets opt-in.

## Memoria

`project_coinnect.md`, `project_coinnect_strategy.md`, `project_pentest_20260406.md`.
