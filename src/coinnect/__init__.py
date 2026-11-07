# Seconds between background rate refreshes (main._refresh_loop). Was 180 until
# 2026-11-07: Miguel moved it to 5 minutes to cut CPU on a low-traffic service.
REFRESH_INTERVAL_S = 300
