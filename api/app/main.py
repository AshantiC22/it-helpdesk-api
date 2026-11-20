"""IT Helpdesk API.

Endpoints are added here as the project grows:
  Session 8  - /health
  Session 9  - people and devices
  Session 10 - tickets
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
import psycopg
from datetime import datetime, timedelta, timezone

from app.db import get_connection

app = FastAPI(title="IT Helpdesk API")

# The allowed values, kept in one place so the API and the database agree.
ROLES = ("requester", "technician", "admin")
DEVICE_TYPES = ("laptop", "desktop", "printer", "switch", "access_point")
DEVICE_STATUSES = ("in_service", "in_repair", "retired")
TICKET_CATEGORIES = ("hardware", "software", "network", "account")
TICKET_PRIORITIES = ("low", "medium", "high", "urgent")
TICKET_STATUSES = ("open", "in_progress", "waiting_on_user", "resolved", "closed")

# R4: the server decides the due date. The client only picks a priority.
DUE_AFTER = {
    "urgent": timedelta(hours=4),
    "high": timedelta(hours=24),
    "medium": timedelta(days=3),
    "low": timedelta(days=7),
}


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


# ---------- Tickets ----------

class TicketIn(BaseModel):
    """The body of POST /tickets.

    What is NOT here is the point: id, status, created_at, due_at, resolved_at
    and resolution_note are all decided by the server or the database. A client
    cannot set them, because a field that is absent from the model is discarded
    before this code ever runs.
    """
    title: str = Field(min_length=1)
    description: str | None = None
    category: str = Field(pattern="^(hardware|software|network|account)$")
    priority: str = Field(pattern="^(low|medium|high|urgent)$")
    requester_id: int
    technician_id: int | None = None
    device_id: int | None = None


@app.post("/tickets", status_code=201)
def create_ticket(payload: TicketIn):
    """Opens a ticket.

    404 if requester_id, technician_id or device_id points at a row that is not there.
    409 if that device already has a ticket that is not resolved or closed (R7).
    """
    # One clock for both columns. created_at and due_at have to agree exactly,
    # so they are both derived from this single reading, in UTC.
    now = datetime.now(timezone.utc)
    due_at = now + DUE_AFTER[payload.priority]   # R4: priority decides the deadline

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tickets (
                        title, description, category, priority,
                        created_at, due_at,
                        requester_id, technician_id, device_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        payload.title,
                        payload.description,
                        payload.category,
                        payload.priority,
                        now,
                        due_at,
                        payload.requester_id,
                        payload.technician_id,
                        payload.device_id,
                    ),
                )
                return cur.fetchone()

    except psycopg.errors.ForeignKeyViolation:
        raise HTTPException(status_code=404, detail="requester, technician or device not found")
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="that device already has an unresolved ticket")


# The columns every ticket listing returns. Written once so the list endpoint
# and the detail endpoint cannot drift apart.
TICKET_COLUMNS = """
    id, title, description, category, priority, status,
    created_at, due_at, resolved_at, resolution_note,
    requester_id, technician_id, device_id
"""


@app.get("/tickets")
def list_tickets(
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    technician_id: int | None = None,
    overdue: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Lists tickets. Every filter is optional; they combine with AND.

    limit and offset page the results. The response is an envelope so the
    client can tell whether more rows exist without guessing.
    """
    # Reject bad vocabulary before building any SQL.
    if status is not None and status not in TICKET_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {TICKET_STATUSES}")
    if priority is not None and priority not in TICKET_PRIORITIES:
        raise HTTPException(status_code=422, detail=f"priority must be one of {TICKET_PRIORITIES}")
    if category is not None and category not in TICKET_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"category must be one of {TICKET_CATEGORIES}")

    # Build the WHERE clause one condition at a time. The strings appended to
    # `conditions` are written by me and never contain a client value; every
    # client value goes into `params` and travels as a bound parameter.
    conditions: list[str] = []
    params: list[object] = []

    if status is not None:
        conditions.append("status = %s")
        params.append(status)

    if priority is not None:
        conditions.append("priority = %s")
        params.append(priority)

    if category is not None:
        conditions.append("category = %s")
        params.append(category)

    if technician_id is not None:
        conditions.append("technician_id = %s")
        params.append(technician_id)

    if overdue:
        # Past due and still not finished. No client value, so no parameter.
        conditions.append("due_at < now() AND status NOT IN ('resolved', 'closed')")

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    # count(*) OVER () counts the whole filtered set, before LIMIT cuts it down,
    # so the total arrives in this same query instead of a second round trip.
    #
    # ORDER BY ends with id because created_at is not unique. Without that
    # tiebreaker, two tickets sharing a timestamp can swap places between
    # pages and a row gets served twice or skipped entirely.
    sql = f"""
        SELECT {TICKET_COLUMNS}, count(*) OVER () AS total_count
        FROM tickets
        {where}
        ORDER BY created_at DESC, id DESC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()

    if rows:
        total = rows[0]["total_count"]
        for row in rows:
            del row["total_count"]      # an implementation detail, not data
    else:
        # The count rides along on the rows, so an empty page carries no count.
        # That happens when offset is past the end. Ask for the count on its own
        # rather than reporting a total of zero for a set that is not empty.
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT count(*) AS n FROM tickets {where}", tuple(params[:-2]))
                total = cur.fetchone()["n"]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "returned": len(rows),
        "items": rows,
    }


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int):
    """One ticket, with the people and device resolved into names.

    404 if there is no ticket with that id.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    t.id, t.title, t.description, t.category, t.priority, t.status,
                    t.created_at, t.due_at, t.resolved_at, t.resolution_note,
                    r.id            AS requester_id,
                    r.full_name     AS requester_name,
                    r.email         AS requester_email,
                    r.building      AS requester_building,
                    tech.id         AS technician_id,
                    tech.full_name  AS technician_name,
                    d.id            AS device_id,
                    d.asset_tag     AS device_asset_tag,
                    d.type          AS device_type,
                    d.room          AS device_room
                FROM tickets t
                JOIN people r         ON r.id    = t.requester_id
                LEFT JOIN people tech ON tech.id = t.technician_id
                LEFT JOIN devices d   ON d.id    = t.device_id
                WHERE t.id = %s
                """,
                (ticket_id,),
            )
            row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="ticket not found")

    # The query returns one flat row. Nest it so the client gets objects
    # instead of a pile of prefixed column names.
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "category": row["category"],
        "priority": row["priority"],
        "status": row["status"],
        "created_at": row["created_at"],
        "due_at": row["due_at"],
        "resolved_at": row["resolved_at"],
        "resolution_note": row["resolution_note"],
        "requester": {
            "id": row["requester_id"],
            "full_name": row["requester_name"],
            "email": row["requester_email"],
            "building": row["requester_building"],
        },
        "technician": None if row["technician_id"] is None else {
            "id": row["technician_id"],
            "full_name": row["technician_name"],
        },
        "device": None if row["device_id"] is None else {
            "id": row["device_id"],
            "asset_tag": row["device_asset_tag"],
            "type": row["device_type"],
            "room": row["device_room"],
        },
    }