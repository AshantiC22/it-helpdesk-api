CREATE TABLE people(
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE CHECK(email = lower(email)),
    role TEXT NOT NULL CHECK(role IN ('requester','technician','admin')),
    building TEXT NOT NULL,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);  