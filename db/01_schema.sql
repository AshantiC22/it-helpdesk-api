CREATE TABLE people(
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE CHECK(email = lower(email)),
    role TEXT NOT NULL CHECK(role IN ('requester','technician','admin')),
    building TEXT NOT NULL,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
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

















