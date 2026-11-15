-- Report 2: technician workload
-- How many open tickets does each technician have, including technicians with zero?
SELECT p.full_name   AS technician,
       count(t.id)   AS open_tickets          -- count(t.id), not count(*): zero stays zero
FROM people p
LEFT JOIN tickets t
       ON t.technician_id = p.id
      AND t.status NOT IN ('resolved', 'closed')  -- in ON, not WHERE, so Derek is kept
WHERE p.role = 'technician'
GROUP BY p.id, p.full_name
ORDER BY open_tickets DESC, p.full_name;
