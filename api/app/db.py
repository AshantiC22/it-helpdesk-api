"""Database connection. Settings come from environment variables,
so no password is ever written in the code."""
import os
import psycopg
from psycopg.rows import dict_row


def get_connection():
    """Open a connection to Postgres. Rows come back as dictionaries,
    so FastAPI can turn them straight into JSON."""
    return psycopg.connect(
        host=os.environ.get("DB_HOST", "db"),          # the SERVICE name
        port=os.environ.get("DB_PORT", "5432"),        # the CONTAINER port
        dbname=os.environ.get("DB_NAME", "helpdesk"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ["DB_PASSWORD"],            # no default: must be supplied
        row_factory=dict_row,
    )