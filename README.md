# IT Helpdesk API

Back end for a school district IT helpdesk: staff submit tickets, technicians work them, and managers pull reports.

**Planned stack:** Python, FastAPI, PostgreSQL 16, Docker Compose

**Status:** in progress

## Design decisions

**Which columns can be NULL?** Only values that can genuinely be missing: a ticket's
technician (not assigned yet), device (account tickets have none), `resolved_at` and
`resolution_note` (not resolved yet), `description` (the title may say it all), and a
device's `assigned_to` (back in the pool). Everything else is `NOT NULL`.

**TEXT with a CHECK, or lookup tables?** TEXT with a CHECK. The lists are short and rarely
change, so simplicity and no JOINs win. I'd switch to lookup tables if values changed often
or each value needed its own data, like due hours.

**Is the due date calculated or stored?** Stored. The API sets `due_at` once, from the
priority (urgent 4 hours, high 1 day, medium 3 days, low 5 days), because a DEFAULT can't
read other columns. Storing it means old deadlines don't move if the rules change later,
and the overdue report is a simple comparison on one column.

**What happens when a person is deleted?** The database refuses (`ON DELETE RESTRICT`) if
they submitted tickets, are assigned tickets, or wrote comments, so history is never lost
(rule R10). Devices they had become unassigned (`ON DELETE SET NULL`). Comments are deleted
with their ticket (`ON DELETE CASCADE`), because a comment means nothing on its own.

**Is a building plain text or its own table?** Plain text. A small district has few
buildings. I'd switch to a `buildings` table if we needed more about each building, or if
typos like "Purvis Elem" vs "Purvis Elementary" started splitting reports.

**Secure by default:** `comments.is_internal` defaults to `true`, so if the code forgets to
set it, a technician's private note is never shown to the requester.