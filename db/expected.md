# Expected report answers

Worked out from `02_seed.sql` before writing the queries. Each report query must return
exactly these rows. Run them right after a rebuild (`docker compose down -v`, then `up -d`):
the seed's timestamps are relative to the moment it loads.

## 1. Overdue tickets (`reports/overdue.sql`)

Unresolved (not `resolved` or `closed`) and `due_at` in the past, most overdue first.
Hours overdue = hours since created minus the priority's time
(urgent 4, high 24, medium 72, low 120). These grow as time passes; the order does not.

| id | title | priority | requester | technician | hours overdue |
|---|---|---|---|---|---|
| 2 | Gym access point dropping clients | high | Andre Lewis | Tasha Wells | 48.0 (72 - 24) |
| 5 | Request shared drive access | low | Rita Hayes | Unassigned | 40.0 (160 - 120) |
| 3 | Gradebook app crashes on save | high | Nina Park | Unassigned | 30.0 (54 - 24) |
| 4 | Lab 2 desktop will not boot | medium | Kim Foster | Marcus Bell | 28.0 (100 - 72) |
| 1 | Front office printer jammed | urgent | Janet Cole | Marcus Bell | 26.0 (30 - 4) |
| 6 | Locked out before state testing | urgent | Sean Moore | Tasha Wells | 6.0 (10 - 4) |

6 rows. Tickets 3 and 5 have no technician: an INNER JOIN on the technician would wrongly
return only 4 rows.

## 2. Technician workload (`reports/workload.sql`)

Open = `open`, `in_progress` or `waiting_on_user`. Every technician appears, even with zero.

| technician | open tickets |
|---|---|
| Tasha Wells | 4 (tickets 2, 6, 10, 11) |
| Marcus Bell | 3 (tickets 1, 4, 9) |
| Derek Young | 0 |

3 rows. If the status filter sits in WHERE instead of the JOIN's ON, Derek disappears.

## 3. Average resolution time, last 30 days (`reports/resolution_time.sql`, Session 7)

Tickets with `resolved_at` in the last 30 days (tickets 13 to 32). Hours = resolved_at minus
created_at, averaged per category and priority, rounded to 1 decimal. Tickets 33 to 40 were
resolved more than 30 days ago and must not count.

| category | priority | tickets | average hours |
|---|---|---|---|
| account | medium | 1 | 12.0 |
| account | urgent | 1 | 1.0 |
| hardware | high | 3 | 6.7 ((4 + 10 + 6) / 3) |
| hardware | low | 1 | 30.0 |
| hardware | medium | 4 | 21.0 ((6 + 26 + 22 + 30) / 4) |
| hardware | urgent | 1 | 2.0 |
| network | high | 2 | 5.0 ((2 + 8) / 2) |
| network | low | 1 | 50.0 |
| network | medium | 1 | 20.0 |
| network | urgent | 1 | 3.0 |
| software | high | 1 | 5.0 |
| software | low | 2 | 42.0 ((40 + 44) / 2) |
| software | medium | 1 | 18.0 |

13 rows, ordered by category, then priority.

## 4. Repeat devices, top 5 with ties (`reports/repeat_devices.sql`, Session 7)

Tickets per device (all statuses), ranked with RANK(), keeping every device ranked 5 or better.

| rank | asset tag | type | building | tickets |
|---|---|---|---|---|
| 1 | LCSD-00403 | printer | Purvis High | 6 |
| 2 | LCSD-00401 | laptop | Purvis High | 3 |
| 2 | LCSD-00410 | switch | Purvis High | 3 |
| 2 | LCSD-00412 | access_point | Purvis High | 3 |
| 5 | LCSD-00402 | laptop | Purvis High | 2 |
| 5 | LCSD-00404 | printer | Lumberton Middle | 2 |
| 5 | LCSD-00405 | desktop | Lumberton Middle | 2 |
| 5 | LCSD-00406 | desktop | Lumberton Middle | 2 |
| 5 | LCSD-00413 | access_point | Purvis Elementary | 2 |

9 rows. Three devices tie at rank 2, so RANK() skips 3 and 4; five devices tie at rank 5.
