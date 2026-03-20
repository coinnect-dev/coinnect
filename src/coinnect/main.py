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
    md = (DOCS_DIR / "whitepaper.md").read_text()
    # Basic markdown → HTML (no extra dependency)
    import re
    lines = md.split("\n")
    html_lines = []
    for line in lines:
        if line.startswith("# "): line = f"<h1>{line[2:]}</h1>"
        elif line.startswith("## "): line = f"<h2>{line[3:]}</h2>"
        elif line.startswith("### "): line = f"<h3>{line[4:]}</h3>"
        elif line.startswith("---"): line = "<hr>"
        elif line.startswith("- "): line = f"<li>{line[2:]}</li>"
        elif line == "": line = "<br>"
        else: line = f"<p>{line}</p>"
        # inline: bold, code
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        line = re.sub(r'`(.+?)`', r'<code>\1</code>', line)
        html_lines.append(line)
    body = "\n".join(html_lines)
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Coinnect Whitepaper</title>
  <style>
    body {{ max-width: 760px; margin: 0 auto; padding: 2rem 1.5rem; font-family: Georgia, serif; line-height: 1.7; color: #1a1a1a; }}
    h1,h2,h3 {{ font-family: system-ui, sans-serif; }}
    h1 {{ font-size: 2rem; border-bottom: 2px solid #06b6d4; padding-bottom: .5rem; }}
    h2 {{ font-size: 1.4rem; margin-top: 2.5rem; color: #0891b2; }}
    code {{ background: #f1f5f9; padding: .1em .4em; border-radius: 3px; font-size: .9em; }}
    hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 2rem 0; }}
    a {{ color: #06b6d4; }} li {{ margin: .3rem 0; }}
    .back {{ display: inline-block; margin-bottom: 2rem; font-family: system-ui; font-size: .9rem; }}
  </style>
</head>
<body>
  <a class="back" href="/">← Back to Coinnect</a>
  {body}
</body>
</html>""")

