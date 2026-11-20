-- Report 4: devices with the most tickets, top 5 with ties
WITH counts AS (
    SELECT d.asset_tag,
           d.type,
           d.building,
           count(t.id) AS tickets
    FROM devices d
    JOIN tickets t ON t.device_id = d.id
    GROUP BY d.id, d.asset_tag, d.type, d.building
),
ranked AS (
    SELECT *,
           RANK() OVER (ORDER BY tickets DESC) AS rnk
    FROM counts
)
SELECT * FROM ranked
WHERE ____
ORDER BY ____;