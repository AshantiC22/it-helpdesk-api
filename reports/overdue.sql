-- Report 1: overdue tickets
-- Which unresolved tickets are past due, most overdue first,
-- with requester, technician, and hours overdue?
SELECT t.id,
       t.title,
       t.priority,
       r.full_name                                         AS requester,
       COALESCE(tech.full_name, 'Unassigned')              AS technician,
       round(EXTRACT(EPOCH FROM (now() - t.due_at)) / 3600, 1) AS hours_overdue
FROM tickets t
JOIN people r         ON r.id = t.requester_id      -- every ticket has a requester
LEFT JOIN people tech ON tech.id = t.technician_id  -- LEFT: keep unassigned tickets
WHERE t.status NOT IN ('resolved', 'closed')
  AND t.due_at < now()
ORDER BY hours_overdue DESC;
