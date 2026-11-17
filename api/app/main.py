"""IT Helpdesk API. Session 8: health check only."""
from fastapi import FastAPI, HTTPException

from app.db import get_connection

app = FastAPI(title="IT Helpdesk API")


@app.get("/health")
def health():
    """Checks the API and the database. 200 if both are up, 500 if the database is not."""
    try:
        with get_connection() as conn:       # open, and close no matter what
            with conn.cursor() as cur:       # the cursor runs the SQL
                cur.execute("SELECT 1")      # the cheapest possible query
                cur.fetchone()               # proves the database answered
    except Exception:
        raise HTTPException(status_code=500, detail="database unavailable")

    return {"status": "ok", "database": "up"}