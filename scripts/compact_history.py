#!/usr/bin/env python3
"""Compact history.db and reclaim disk. Stop coinnect first: VACUUM needs the DB to itself."""

import sqlite3

from coinnect.db.history import DB_PATH, compact_history

print(f"archived {compact_history()} rows")
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA auto_vacuum=INCREMENTAL")
conn.execute("VACUUM")
conn.close()
print(f"{DB_PATH}: {DB_PATH.stat().st_size // 1048576} MB")
