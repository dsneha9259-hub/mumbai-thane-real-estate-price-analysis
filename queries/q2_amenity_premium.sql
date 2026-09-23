-- Question 2: Do premium amenities (clubhouse, pool, gym) correlate with
-- meaningfully higher price/sqft, or is it mostly marketing?
--
-- Controlled for locality + bedroom, same pattern as Question 1's query.
-- Run once per amenity column (Club House / Swimming Pool / Gymnasium).

WITH locality_bedroom_both AS (
    SELECT "Area Name", bedroom
    FROM properties_clean
    GROUP BY "Area Name", bedroom
    HAVING COUNT(DISTINCT "Club House") = 2
       AND SUM(CASE WHEN "Club House" = 0 THEN 1 ELSE 0 END) >= 3
       AND SUM(CASE WHEN "Club House" = 1 THEN 1 ELSE 0 END) >= 3
)
SELECT
    p."Club House" AS has_amenity,
    COUNT(*) AS n,
    ROUND(AVG(p.price_per_sqft), 0) AS avg_price_per_sqft,
    ROUND(MEDIAN(p.price_per_sqft), 0) AS median_price_per_sqft
FROM properties_clean p
JOIN locality_bedroom_both l
  ON p."Area Name" = l."Area Name" AND p.bedroom = l.bedroom
GROUP BY p."Club House"
ORDER BY p."Club House";

-- Bundling check: are Club House, Swimming Pool and Gymnasium
-- effectively one combined feature rather than three independent ones?
SELECT
    "Club House", "Swimming Pool", "Gymnasium", COUNT(*) AS n
FROM properties_clean
GROUP BY "Club House", "Swimming Pool", "Gymnasium"
ORDER BY n DESC;
