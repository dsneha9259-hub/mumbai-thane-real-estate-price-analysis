-- Question 1: Is there a real "under-construction discount" vs ready-to-move,
-- and how big is it?
--
-- IMPORTANT: A naive comparison (just Ready to Move vs Under Construction averages)
-- is confounded by locality -- certain premium under-construction towers skew the
-- average. This query controls for BOTH bedroom count AND locality, restricting
-- to (locality, bedroom) pairs that have at least 3 listings of each possession
-- type, so the comparison is genuinely apples-to-apples.

WITH locality_bedroom_both AS (
    SELECT "Area Name", bedroom
    FROM properties_clean
    WHERE possession_simplified IS NOT NULL
    GROUP BY "Area Name", bedroom
    HAVING COUNT(DISTINCT possession_simplified) = 2
       AND SUM(CASE WHEN possession_simplified = 'Ready to Move' THEN 1 ELSE 0 END) >= 3
       AND SUM(CASE WHEN possession_simplified = 'Under Construction' THEN 1 ELSE 0 END) >= 3
)
SELECT
    p.bedroom,
    p.possession_simplified,
    COUNT(*) AS n,
    ROUND(AVG(p.price_per_sqft), 0) AS avg_price_per_sqft,
    ROUND(MEDIAN(p.price_per_sqft), 0) AS median_price_per_sqft
FROM properties_clean p
JOIN locality_bedroom_both l
  ON p."Area Name" = l."Area Name" AND p.bedroom = l.bedroom
WHERE p.possession_simplified IS NOT NULL
GROUP BY p.bedroom, p.possession_simplified
ORDER BY p.bedroom, p.possession_simplified;
