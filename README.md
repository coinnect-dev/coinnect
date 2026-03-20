# Coinnect

> The open routing layer for global money.

**coinnect.bot** · Non-profit · Open source · Bot-friendly

---

## What is Coinnect?

Coinnect finds the cheapest path to send money between any two currencies — across traditional remittance services, crypto exchanges, and regional P2P platforms.

You tell it where money needs to go. It tells you how to get there, ranked by cost and time. It never touches your funds.

```
GET https://api.coinnect.bot/v1/quote?from=USD&to=NGN&amount=500
```

```json
{
  "routes": [
    {
      "rank": 1,
      "label": "Cheapest",
      "total_cost_pct": 1.4,
      "total_time_minutes": 60,
      "steps": [
        { "from": "USD", "to": "USDC", "via": "Kraken",     "fee_pct": 0.5 },
        { "from": "USDC", "to": "NGN",  "via": "YellowCard", "fee_pct": 0.9 }
      ],
      "you_send": 500.00,
      "they_receive": 762450,
      "vs_western_union_saving_usd": 21.50
    }
  ]
}
```

## Why non-profit?

Every comparison platform faces the same problem: the business model eventually compromises the product. Affiliate commissions, promoted listings, premium placements — these are not malicious choices, they are business necessities. But they introduce bias into what should be a purely informational service.

Coinnect accepts no commission from any exchange, ever. It is funded by voluntary donations from users who save money using it.

## For humans and machines

**Humans** use the web interface at [coinnect.bot](https://coinnect.bot): enter amount, origin, destination — get a ranked table of routes with step-by-step instructions.

**Machines** query the public REST API directly. Coinnect is designed to be called as a tool by AI agents, chatbots, and automated systems. Full OpenAPI spec in [`/docs/api`](./docs/api/).

## The problem we solve

Global money flows through dozens of closed ecosystems — M-Pesa, GCash, bKash, UPI, Alipay, Western Union, regional P2P platforms — that don't speak to each other. Moving money between them requires knowing which path exists, which is cheapest today, and how many steps it takes.

That information exists. It's just fragmented, opaque, and — when someone organizes it — monetized through referral fees that bias the result.

Coinnect organizes it without bias. No referral fees. No promoted routes. No equity. No exit.

## Status

🚧 **Pre-launch** — targeting May 1, 2026

- [x] White paper (v0.3)
- [ ] OpenAPI spec
- [ ] Quote engine (MVP: 6 exchanges)
- [ ] Web UI
- [ ] Public API

## White paper

Full white paper in [`/docs/whitepaper.md`](./docs/whitepaper.md).

## Contributing

Coinnect is open source. Contributions welcome — exchange integrations, routing improvements, translations, and documentation.

See [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Founder

Miguel Valencia Villaseñor — former COO at Airtm (2018–2025).

Built Coinnect because the problem is real, the solution is simple, and no one was building it without a business model attached.

Public donation wallet: *forthcoming at coinnect.bot*

## License

MIT — free to use, fork, and build on.
