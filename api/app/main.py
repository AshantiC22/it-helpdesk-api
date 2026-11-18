"""IT Helpdesk API.

Endpoints are added here as the project grows:
  Session 8  - /health
  Session 9  - people and devices
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
import psycopg

from app.db import get_connection

app = FastAPI(title="IT Helpdesk API")

# The allowed values, kept in one place so the API and the database agree.
ROLES = ("requester", "technician", "admin")
DEVICE_TYPES = ("laptop", "desktop", "printer", "switch", "access_point")
DEVICE_STATUSES = ("in_service", "in_repair", "retired")


# ---------- Request models ----------

class PersonIn(BaseModel):
    """The body of POST /people. FastAPI returns 422 if it does not match."""
    full_name: str = Field(min_length=1)
    email: EmailStr
    role: str = Field(pattern="^(requester|technician|admin)$")
    building: str = Field(min_length=1)


# ---------- Health ----------

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


# ---------- People ----------

@app.post("/people", status_code=201)
def create_person(person: PersonIn):
    """Adds a person. 409 if the email is already registered."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO people (full_name, email, role, building)
                       VALUES (%s, %s, %s, %s)
                       RETURNING id, full_name, email, role, building, joined_at""",
                    (person.full_name, person.email.lower(), person.role, person.building),
                )
                return cur.fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="A person with that email already exists")


@app.get("/people")
def list_people(role: str | None = None):
    """Lists people, optionally filtered by role."""
    if role is not None and role not in ROLES:
        raise HTTPException(status_code=422, detail=f"role must be one of {ROLES}")

    with get_connection() as conn:
        with conn.cursor() as cur:
            if role is None:
                cur.execute(
                    """SELECT id, full_name, email, role, building, joined_at
                       FROM people
                       ORDER BY full_name"""
                )
            else:
                cur.execute(
                    """SELECT id, full_name, email, role, building, joined_at
                       FROM people
                       WHERE role = %s
                       ORDER BY full_name""",
                    (role,),
                )
            return cur.fetchall()


# ---------- Devices ----------

class DeviceIn(BaseModel):
    """The body of POST /devices. status is left out: the database defaults it."""
    asset_tag: str = Field(min_length=1)
    type: str = Field(pattern="^(laptop|desktop|printer|switch|access_point)$")
    building: str = Field(min_length=1)
    room: str = Field(min_length=1)
    assigned_to: int | None = None        # optional: a person's id, or nobody


@app.post("/devices", status_code=201)
def create_device(device: DeviceIn):
    """Adds a device. 409 if the asset tag is already in use."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO devices (asset_tag, type, building, room, assigned_to)
                       VALUES (%s, %s, %s, %s, %s)
                       RETURNING id, asset_tag, type, building, room, status, assigned_to""",
                    (device.asset_tag, device.type, device.building,
                     device.room, device.assigned_to),
                )
                return cur.fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="A device with that asset tag already exists")


@app.get("/devices")
def list_devices(status: str | None = None):
    """Lists devices, optionally filtered by status."""
    if status is not None and status not in DEVICE_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {DEVICE_STATUSES}")

    with get_connection() as conn:
        with conn.cursor() as cur:
            if status is None:
                cur.execute(
                    """SELECT id, asset_tag, type, building, room, status, assigned_to
                       FROM devices
                       ORDER BY asset_tag"""
                )
            else:
                cur.execute(
                    """SELECT id, asset_tag, type, building, room, status, assigned_to
                       FROM devices
                       WHERE status = %s
                       ORDER BY asset_tag""",
                    (status,),
                )
            return cur.fetchall()