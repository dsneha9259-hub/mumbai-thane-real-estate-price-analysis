-- Question 4 (locality-level rollup, after residuals are computed in Python --
-- see notebook/script -- this query does the final SQL-side aggregation once
-- predicted_psf and residual_pct exist as columns):
--
-- Ranks localities (min. 30 listings) by how much cheaper/pricier they are
-- than what their bedroom/bathroom/floor/furnishing/amenity mix would predict.

SELECT
    "Area Name",
    COUNT(*) AS n,
    ROUND(AVG(price_per_sqft), 1) AS avg_actual_psf,
    ROUND(AVG(predicted_psf), 1) AS avg_predicted_psf,
    ROUND(AVG(residual_pct), 1) AS avg_residual_pct
FROM properties_with_residuals
GROUP BY "Area Name"
HAVING COUNT(*) >= 30
ORDER BY avg_residual_pct ASC;
