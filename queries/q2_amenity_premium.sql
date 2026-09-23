-- Question 2: Do premium amenities (clubhouse, pool, gym) correlate with
-- meaningfully higher price/sqft, or is it mostly marketing?
--
-- Club House, Swimming Pool and Gymnasium co-occur in ~95% of listings
-- (either all three present or none) -- so they are tested here as ONE
-- combined "amenity bundle" flag, not as three independent features.
-- Controlled for locality + bedroom, same pattern as Question 1's query.

WITH properties_with_bundle AS (
    SELECT *,
        CASE WHEN "Club House" = 1 AND "Swimming Pool" = 1 AND "Gymnasium" = 1
             THEN 1 ELSE 0 END AS has_amenity_bundle
    FROM properties_clean
),
locality_bedroom_both AS (
    SELECT "Area Name", bedroom
    FROM properties_with_bundle
    GROUP BY "Area Name", bedroom
    HAVING COUNT(DISTINCT has_amenity_bundle) = 2
       AND SUM(CASE WHEN has_amenity_bundle = 0 THEN 1 ELSE 0 END) >= 3
       AND SUM(CASE WHEN has_amenity_bundle = 1 THEN 1 ELSE 0 END) >= 3
)
SELECT
    p.has_amenity_bundle,
    COUNT(*) AS n,
    ROUND(AVG(p.price_per_sqft), 0) AS avg_price_per_sqft,
    ROUND(MEDIAN(p.price_per_sqft), 0) AS median_price_per_sqft
FROM properties_with_bundle p
JOIN locality_bedroom_both l
  ON p."Area Name" = l."Area Name" AND p.bedroom = l.bedroom
GROUP BY p.has_amenity_bundle
ORDER BY p.has_amenity_bundle;

-- Bundling check: are Club House, Swimming Pool and Gymnasium
-- effectively one combined feature rather than three independent ones?
SELECT
    "Club House", "Swimming Pool", "Gymnasium", COUNT(*) AS n
FROM properties_clean
GROUP BY "Club House", "Swimming Pool", "Gymnasium"
ORDER BY n DESC;
