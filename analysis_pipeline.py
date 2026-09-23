"""
Mumbai/Thane Real Estate Analysis — Cleaning & Modeling Pipeline
==================================================================
Reproduces the cleaning steps and the Python-based analysis used for
Questions 3 (price/sqft drivers), 4 (locality value residuals), and
5 (loading factor vs. developer pricing).

Questions 1 and 2 are answered via SQL directly on the cleaned CSV
this script produces (see /queries/).

Input:  properties.csv (raw, 12,685 rows x 145 cols, from Kaggle)
Output: properties_clean.csv (9,980 rows, cleaned + feature-engineered)
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

# ---------------------------------------------------------------------------
# PHASE 1-2: LOAD & CLEAN
# ---------------------------------------------------------------------------
df = pd.read_csv('properties.csv', low_memory=False)
print("Starting rows:", len(df))

# Restrict to core Mumbai Metropolitan Region (Mumbai + Thane).
# The raw "City" column contains ~30 stray rows from other cities
# (Kalyan, Hyderabad, Nagpur, Palghar, Bhiwandi, Agartala, Gurgaon) —
# clearly scraping noise, not genuine Mumbai-market listings.
df = df[df['City'].isin(['Mumbai', 'Thane'])].copy()

# Drop missing/zero/extreme-outlier prices. The raw data contains
# obvious data-entry errors (e.g. a ₹4,080 Cr 2BHK) that would
# distort every downstream statistic if left in.
df = df[df['Price'].notna() & (df['Price'] > 100000) & (df['Price'] < 500000000)]

# Drop rows missing Carpet Area or with implausible values.
df = df[df['Carpet Area'].notna() & (df['Carpet Area'] > 100) & (df['Carpet Area'] < 10000)]

# Carpet Area can never exceed Covered Area (carpet area is, by definition,
# the usable space inside the covered/built-up area) — 85 rows violated
# this and were dropped as data errors.
df = df[(df['Covered Area'].isna()) | (df['Carpet Area'] <= df['Covered Area'])]

# Restrict to actual sale listings (drop Rent/Rent-Lease/Other — a
# fundamentally different pricing model that shouldn't be mixed in).
df = df[df['Transaction Type'].isin(['Resale', 'New Property'])]

# Compute price-per-sqft ourselves rather than trusting the dataset's
# own "sqft Price" column, which contains clearly broken values
# (max of ₹3.4 crore/sqft in the raw data).
df['price_per_sqft'] = df['Price'] / df['Carpet Area']

# Loading factor = usable (carpet) area as a fraction of built-up
# (covered) area. This is the field an architecture background
# specifically flags as meaningful — it's rarely used in generic
# data-analytics tutorials.
df['loading_factor'] = np.where(
    df['Covered Area'].notna(), df['Carpet Area'] / df['Covered Area'], np.nan
)

# Simplify Possession Status: any future-dated entry (e.g. "Dec '26")
# is still, functionally, under construction.
def simplify_possession(x):
    if x == 'Ready to Move':
        return 'Ready to Move'
    elif x == 'Under Construction':
        return 'Under Construction'
    elif pd.isna(x):
        return np.nan
    else:
        return 'Under Construction'
df['possession_simplified'] = df['Possession Status'].apply(simplify_possession)

# Clean the Floor No field: "Ground" -> 0, "Upper/Lower Basement" -> -1.
def clean_floor(x):
    if pd.isna(x):
        return np.nan
    x = str(x).strip()
    if x == 'Ground':
        return 0
    if 'Basement' in x:
        return -1
    try:
        return float(x)
    except ValueError:
        return np.nan
df['floor_clean'] = df['Floor No'].apply(clean_floor)

# Club House, Swimming Pool and Gymnasium co-occur in ~95% of listings
# (either all three or none) — treated as one bundled amenity flag
# rather than three independent features.
df['has_amenity_bundle'] = (
    (df['Club House'] == 1) & (df['Swimming Pool'] == 1) & (df['Gymnasium'] == 1)
).astype(int)

print("Final clean row count:", len(df))

keep_cols = ['ID', 'City', 'Area Name', 'Location', 'Price', 'Carpet Area', 'Covered Area',
             'price_per_sqft', 'loading_factor', 'bedroom', 'Bathroom', 'Floor No', 'floor_clean',
             'Facing', 'furnished Type', 'Possession Status', 'possession_simplified',
             'Transaction Type', 'Developer', 'Club House', 'Swimming Pool', 'Gymnasium',
             'has_amenity_bundle', 'Lift', 'Security', 'Parking', 'Power Back Up',
             'Rain Water Harvesting', 'Park', 'Water Storage']
clean_df = df[keep_cols].copy()
clean_df.to_csv('properties_clean.csv', index=False)


# ---------------------------------------------------------------------------
# QUESTION 3: What drives price per sqft?
# ---------------------------------------------------------------------------
locality_counts = clean_df['Area Name'].value_counts()
common_localities = locality_counts[locality_counts >= 30].index
clean_df['locality_grouped'] = clean_df['Area Name'].where(
    clean_df['Area Name'].isin(common_localities), 'Other'
)

model_df = clean_df[['price_per_sqft', 'bedroom', 'Bathroom', 'floor_clean', 'furnished Type',
                      'possession_simplified', 'locality_grouped', 'has_amenity_bundle']].dropna()

target = model_df['price_per_sqft']
features = pd.get_dummies(
    model_df.drop(columns=['price_per_sqft']),
    columns=['furnished Type', 'possession_simplified', 'locality_grouped']
).astype(float)

X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)
rf = RandomForestRegressor(n_estimators=300, max_depth=12, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
print("Q3 — R^2 on test set:", round(r2_score(y_test, rf.predict(X_test)), 3))

# NOTE: bedroom and Bathroom are correlated at r=0.848 (essentially both
# measure "unit size") — reported together as one combined driver rather
# than treating "Bathroom > bedroom in importance" as a standalone finding.


# ---------------------------------------------------------------------------
# QUESTION 4: Which localities offer the best value for their characteristics?
# ---------------------------------------------------------------------------
# Predict price/sqft from property characteristics ONLY (no locality),
# then see which localities are systematically cheaper/pricier than
# their characteristics alone would predict.
model_df2 = clean_df[['price_per_sqft', 'bedroom', 'Bathroom', 'floor_clean', 'furnished Type',
                       'possession_simplified', 'has_amenity_bundle', 'Area Name']].dropna()

features2 = pd.get_dummies(
    model_df2.drop(columns=['price_per_sqft', 'Area Name']),
    columns=['furnished Type', 'possession_simplified']
).astype(float)

rf2 = RandomForestRegressor(n_estimators=300, max_depth=10, random_state=42, n_jobs=-1)
rf2.fit(features2, model_df2['price_per_sqft'])

model_df2['predicted_psf'] = rf2.predict(features2)
model_df2['residual_pct'] = (
    (model_df2['price_per_sqft'] - model_df2['predicted_psf']) / model_df2['predicted_psf'] * 100
)
model_df2.to_csv('properties_with_residuals.csv', index=False)
# See queries/q4_locality_value_residuals.sql for the final locality-level rollup.

# CAVEAT: this measures value relative to bedroom/bathroom/amenity mix only —
# it does NOT account for commute time or proximity to job centers, both of
# which materially affect what "value" means to a real buyer.


# ---------------------------------------------------------------------------
# QUESTION 5: Loading factor vs. developer pricing
# ---------------------------------------------------------------------------
lf_df = clean_df[clean_df['loading_factor'].notna() & clean_df['Developer'].notna()].copy()

# Locality-demean price so we're comparing each listing to its own
# neighborhood's average, not the citywide average.
lf_df['locality_avg_price'] = lf_df.groupby('Area Name')['price_per_sqft'].transform('mean')
lf_df['price_demeaned'] = lf_df['price_per_sqft'] - lf_df['locality_avg_price']

# Locality-demean loading factor the same way, so the correlation below
# isn't confounded by "premium areas happen to have different building styles."
lf_df['locality_avg_loading'] = lf_df.groupby('Area Name')['loading_factor'].transform('mean')
lf_df['loading_demeaned'] = lf_df['loading_factor'] - lf_df['locality_avg_loading']

# Market-wide correlation, controlled for locality (the ~ -0.05 figure
# reported in the dashboard and README).
market_corr = lf_df['loading_demeaned'].corr(lf_df['price_demeaned'])
print(f"Q5 — Locality-controlled correlation (loading factor vs price/sqft): {round(market_corr, 3)}")

lf_df.to_csv('properties_with_demeaned_price.csv', index=False)

# Developer-level rollup threshold: 10+ listings (matches the dashboard note).
dev_counts = lf_df['Developer'].value_counts()
common_devs = dev_counts[dev_counts >= 10].index
print(f"Q5 — Developers with 10+ listings: {len(common_devs)}")
# See queries/q5_loading_factor_by_developer.sql for the final developer-level rollup.

print("\nPipeline complete. Outputs: properties_clean.csv, "
      "properties_with_residuals.csv, properties_with_demeaned_price.csv")
