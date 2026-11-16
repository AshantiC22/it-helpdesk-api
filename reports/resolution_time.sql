-- Report 3: average resolution time by category and priority, last 30 days
SELECT category,
       priority,
       count(*) AS tickets,
       round(avg(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600), 1) AS avg_hours
FROM tickets
WHERE resolved_at >= now() - interval '30 days'
GROUP BY category, priority
ORDER BY category, priority;