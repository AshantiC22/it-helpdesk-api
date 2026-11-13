CREATE TABLE people (
    id        INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name TEXT NOT NULL,
    email     TEXT NOT NULL UNIQUE CHECK (email = lower(email)),
    role      TEXT NOT NULL CHECK (role IN ('requester', 'technician', 'admin')),
    building  TEXT NOT NULL,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE devices (
    id          INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    asset_tag   TEXT NOT NULL UNIQUE,
    type        TEXT NOT NULL CHECK (type IN ('laptop', 'desktop', 'printer', 'switch', 'access_point')),
    building    TEXT NOT NULL,
    room        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'in_service' CHECK (status IN ('in_service', 'in_repair', 'retired')),
    assigned_to INT REFERENCES people(id) ON DELETE SET NULL
);

CREATE TABLE tickets (
    id              INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title           TEXT NOT NULL,
    description     TEXT,
    category        TEXT NOT NULL CHECK (category IN ('hardware', 'software', 'network', 'account')),
    priority        TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    status          TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'waiting_on_user', 'resolved', 'closed')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    due_at          TIMESTAMPTZ NOT NULL,
    resolved_at     TIMESTAMPTZ,
    resolution_note TEXT,
    requester_id    INT NOT NULL REFERENCES people(id) ON DELETE RESTRICT,
    technician_id   INT REFERENCES people(id) ON DELETE RESTRICT,
    device_id       INT REFERENCES devices(id) ON DELETE SET NULL
);

CREATE TABLE comments (
    id          INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticket_id   INT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    author_id   INT NOT NULL REFERENCES people(id) ON DELETE RESTRICT,
    body        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_internal BOOLEAN NOT NULL DEFAULT true
);























