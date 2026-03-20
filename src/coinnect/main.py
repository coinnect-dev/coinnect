"""
Coinnect API — entry point
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from coinnect.api.routes import router

STATIC_DIR = Path(__file__).parent / "static"
DOCS_DIR = Path(__file__).parent.parent.parent / "docs"

app = FastAPI(
    title="Coinnect API",
    description=(
        "The open routing layer for global money.\n\n"
        "Finds the cheapest path to send money between any two currencies — "
        "across traditional remittance, crypto exchanges, and P2P platforms.\n\n"
        "Non-profit. No affiliate fees. No custody. No KYC.\n\n"
        "**For AI agents:** call `/v1/quote` as a tool with `from`, `to`, and `amount` parameters."
    ),
    version="0.1.0",
    contact={"name": "Coinnect", "url": "https://coinnect.bot"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/whitepaper", include_in_schema=False)
async def whitepaper():
    import markdown as md_lib
    text = (DOCS_DIR / "whitepaper.md").read_text()
    body = md_lib.markdown(text, extensions=["tables", "fenced_code", "nl2br"])
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Coinnect Whitepaper</title>
  <style>
    body {{ max-width: 760px; margin: 0 auto; padding: 2rem 1.5rem; font-family: Georgia, serif; line-height: 1.7; color: #1a1a1a; }}
    h1,h2,h3 {{ font-family: system-ui, sans-serif; margin-top: 2rem; }}
    h1 {{ font-size: 2rem; border-bottom: 2px solid #06b6d4; padding-bottom: .5rem; margin-top: 0; }}
    h2 {{ font-size: 1.4rem; margin-top: 2.5rem; color: #0891b2; }}
    h3 {{ font-size: 1.1rem; color: #374151; }}
    code {{ background: #f1f5f9; padding: .1em .4em; border-radius: 3px; font-size: .9em; }}
    pre {{ background: #f1f5f9; padding: 1rem; border-radius: 6px; overflow-x: auto; }}
    pre code {{ background: none; padding: 0; }}
    hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 2rem 0; }}
    a {{ color: #06b6d4; }}
    li {{ margin: .3rem 0; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1.5rem 0; font-family: system-ui; font-size: .9rem; }}
    th {{ background: #0891b2; color: white; text-align: left; padding: .5rem .75rem; }}
    td {{ padding: .5rem .75rem; border-bottom: 1px solid #e2e8f0; }}
    tr:nth-child(even) td {{ background: #f8fafc; }}
    .back {{ display: inline-block; margin-bottom: 2rem; font-family: system-ui; font-size: .9rem; text-decoration: none; color: #6b7280; }}
    .back:hover {{ color: #06b6d4; }}
  </style>
</head>
<body>
  <a class="back" href="/">← Back to Coinnect</a>
  {body}
</body>
</html>""")

