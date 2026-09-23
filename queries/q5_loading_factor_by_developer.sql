-- Question 5: Does loading factor (carpet/covered area) vary by developer,
-- and do developers with worse loading factor still charge a premium?
--
-- price_demeaned = price_per_sqft minus that property's own locality average,
-- so a positive value means "priced above what's typical for this neighborhood"
-- -- computed in Python (locality-level groupby.transform), then aggregated here.

SELECT
    "Developer",
    COUNT(*) AS n,
    ROUND(AVG(loading_factor), 3) AS avg_loading_factor,
    ROUND(AVG(price_demeaned), 0) AS avg_price_vs_locality_avg
FROM properties_with_demeaned_price
WHERE "Developer" IS NOT NULL
GROUP BY "Developer"
HAVING COUNT(*) >= 10  -- 10+ listings per developer, matching the dashboard note
ORDER BY avg_loading_factor ASC;
