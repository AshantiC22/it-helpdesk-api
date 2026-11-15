-- Break-it tests: every statement after the setup MUST fail.
-- Runs inside a transaction and rolls back, so nothing is saved.
\set ON_ERROR_ROLLBACK on
BEGIN;

-- Setup: just enough data to break things against
INSERT INTO people (full_name, email, role, building) VALUES
    ('Test Requester', 'requester@lcsd.org', 'requester', 'Purvis High'),
    ('Test Tech', 'tech@lcsd.org', 'technician', 'District Office');
INSERT INTO devices (asset_tag, type, building, room)
VALUES ('LCSD-90001', 'printer', 'Purvis High', 'B-104');
INSERT INTO tickets (title, category, priority, due_at, requester_id, device_id)
VALUES ('Printer jam', 'hardware', 'high', now() + interval '1 day',
        (SELECT id FROM people WHERE email = 'requester@lcsd.org'),
        (SELECT id FROM devices WHERE asset_tag = 'LCSD-90001'));

-- R1: email with capital letters
INSERT INTO people (full_name, email, role, building)
VALUES ('Caps Lock', 'Caps@LCSD.org', 'requester', 'Purvis High');

-- R2: status not in the list
INSERT INTO tickets (title, category, priority, status, due_at, requester_id)
VALUES ('Test', 'hardware', 'low', 'pending', now() + interval '5 days',
        (SELECT id FROM people WHERE email = 'requester@lcsd.org'));

-- R3: requester who doesn't exist
INSERT INTO tickets (title, category, priority, due_at, requester_id)
VALUES ('Test', 'hardware', 'low', now() + interval '5 days', 99999);

-- R7: a second open ticket on the same printer
INSERT INTO tickets (title, category, priority, due_at, requester_id, device_id)
VALUES ('Test', 'hardware', 'low', now() + interval '5 days',
        (SELECT id FROM people WHERE email = 'requester@lcsd.org'),
        (SELECT id FROM devices WHERE asset_tag = 'LCSD-90001'));

-- R9: resolved before it was created
INSERT INTO tickets (title, category, priority, status, due_at, resolved_at, resolution_note, requester_id)
VALUES ('Test', 'hardware', 'low', 'resolved', now() + interval '5 days',
        now() - interval '1 day', 'fixed',
        (SELECT id FROM people WHERE email = 'requester@lcsd.org'));

-- R10: delete a person who has a ticket
DELETE FROM people WHERE email = 'requester@lcsd.org';

ROLLBACK;