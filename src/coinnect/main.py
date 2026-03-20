"""
Coinnect API — entry point
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from coinnect.api.routes import router

STATIC_DIR = Path(__file__).parent / "static"

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
