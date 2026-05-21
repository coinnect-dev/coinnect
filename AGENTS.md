<!-- KOA-MANUAL -->
# AGENTS.md — Coinnect

> Cross-agente. **Nota:** este repo NO está dentro de `~/koa/`. Es repo independiente en Forgejo `git.koanet/inge/coinnect`. La actividad aquí no se registra en `~/koa/04_llm/activity.jsonl` salvo que pases `KOA_ACTIVITY_LEDGER` a `koa-bootstrap`.

## Qué es

Exchange router multi-corredor: stable → MXN/local con rutas rankeadas. Web `coinnect.bot`. API `/v1/quote?from=USD&to=MXN&amount=500`. ~80 adapters activos (Kraken, Binance, Coinbase, Bitso CCXT + Wise + Yellow Card + WU + MoneyGram + más).

## Stack

- FastAPI + CCXT + Wise SDK.
- SQLite `data/history.db`.
- Background refresh cada 3 min.
- MCP server: `python -m coinnect.mcp_server` (tools `coinnect_quote`, `coinnect_corridors`, `coinnect_explain_route`).

## Build & Deploy

```bash
cd /home/inge/coinnect
pip install -e .[dev]
pytest
# deploy
rsync -avz . inge@100.64.0.1:/home/inge/coinnect/
ssh inge@100.64.0.1 "systemctl --user restart coinnect"
curl -fsS https://coinnect.bot/v1/quote?from=USD\&to=MXN\&amount=500 | head
```

Servicio prod: ash:8100 (`coinnect.service`).

## Reglas

- Cero credenciales hardcoded. Wise API key vía env. Exchange APIs vía CCXT + env keys.
- Adapters son plugins en `coinnect/adapters/*.py`. Agregar nuevo = nueva clase + registry.
- Ratings en `data/history.db` informan ranking. NO eliminar histórico.
- Pentest 2026-04-07: XSS reflected/stored fixed, HSTS al origin OK. Cloudflare HSTS edge sigue 0 (toggle pendiente Miguel).

## Pendientes

- Cloudflare HSTS edge.
- Cartera Nigeria (60+ rails, sesión 2026-03-28).
- Webhook secrets opt-in.

## Memoria

`project_coinnect.md`, `project_coinnect_strategy.md`, `project_pentest_20260406.md`.
