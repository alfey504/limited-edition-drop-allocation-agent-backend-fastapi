# Regional Demand Drivers — Reference for the Inventory-Allocation Agent

Source: `data/raw/StockX-Data-Contest-2019-3.csv`, aggregated to one row per
(Sneaker Name, Buyer Region) — 50 sneakers x 51 regions = 2,550 rows, same
grid as `new_product_df` in `notebooks/modeling_new_product.ipynb`.
Reproducible via the "EDA" cells in that notebook (cells following
`region_warehouse_capacity`) — sections below map 1:1 onto EDA cells 1-6.
Every finding here (except section 1's raw totals, which come from the full
grid before feature-engineering) is computed from `new_product_df` alone —
no raw transaction-level Sale Price data is used anywhere in this report.

This file is meant to be read by an allocation agent as context, alongside
the trained model's predicted demand for a specific SKU. It contains static,
product-independent facts about how demand is distributed, so the agent has
something to reason from beyond a bare number per region.

## 1. Regional demand is highly concentrated (EDA 1)

Full breakdown, all 51 regions, sorted by share of total historical demand
(region, total units sold historically, % share):

```
California            19349   19.358%
New York              16525   16.532%
Oregon                 7681    7.684%
Florida                6376    6.379%
Texas                  5876    5.879%
New Jersey             4720    4.722%
Illinois               3782    3.784%
Pennsylvania           3109    3.110%
Massachusetts          2903    2.904%
Michigan               2762    2.763%
Virginia               2058    2.059%
Ohio                   1890    1.891%
Maryland               1870    1.871%
Washington             1863    1.864%
Georgia                1846    1.847%
Arizona                1398    1.399%
North Carolina         1344    1.345%
Delaware               1242    1.243%
Connecticut            1110    1.110%
Indiana                1026    1.026%
Colorado                954    0.954%
Wisconsin               840    0.840%
Nevada                  790    0.790%
Tennessee               731    0.731%
Minnesota               725    0.725%
Missouri                660    0.660%
South Carolina          570    0.570%
Louisiana               537    0.537%
Kentucky                488    0.488%
Iowa                    460    0.460%
Alabama                 457    0.457%
Utah                    450    0.450%
Oklahoma                412    0.412%
Hawaii                  383    0.383%
Rhode Island            347    0.347%
Kansas                  340    0.340%
District of Columbia    271    0.271%
Nebraska                245    0.245%
New Hampshire           241    0.241%
New Mexico              231    0.231%
Arkansas                173    0.173%
West Virginia           166    0.166%
Mississippi             163    0.163%
Maine                   132    0.132%
Idaho                   107    0.107%
Vermont                  84    0.084%
North Dakota              64    0.064%
Alaska                    61    0.061%
South Dakota              55    0.055%
Montana                   49    0.049%
Wyoming                   40    0.040%
```

Top 5 regions = 55.8% of all demand. Top 10 = 73.1%. Bottom 10 = 0.9%.
Demand is not close to uniform across regions — an equal 51-way split would
be a bad default.

## 2. This regional split is nearly the same for every product (EDA 2-3)

Method: for each brand/silhouette, normalize its regional totals into a
share vector (sums to 1), then Pearson-correlate that vector against the
pooled overall share vector above. High correlation = that product's
regional preference pattern matches the general pattern; low correlation
would mean the product sells disproportionately in different regions than
sneakers overall.

Brand-vs-brand (share vectors correlated against each other directly):
```
corr(Yeezy region-share, Off-White region-share) = 0.988
```

Silhouette-vs-overall (each silhouette's share vector vs. the pooled one):
```
Yeezy-Boost     0.999   (n=72,162 units)
Air-Presto      0.993   (n=4,363)
Blazer          0.992   (n=3,622)
Air-Max         0.989   (n=3,390)
Air-Force       0.980   (n=2,486)
Zoom-Fly        0.976   (n=4,317)
Air-VaporMax    0.972   (n=3,429)
Hyperdunk       0.970   (n=484)
Air-Jordan      0.957   (n=5,703)   <- lowest of the nine, still very high
```

Interpretation: brand and silhouette mostly change how MUCH total demand a
sneaker gets, not WHERE that demand goes. A brand-new SKU with zero sales
history can still be allocated with high confidence using the fixed
regional-share curve in section 1, scaled to the model's predicted total.

## 3. What actually drives total volume (not regional split) (EDA 4)

Group means of totalItemsSold by category, and the coefficient of variation
(CV = stdev/mean of the group means) as a rough "how much this matters" scale.

```
Feature              CV      Highest-mean group              Lowest-mean group
brand                0.84    Yeezy (70.7)                    Off-White (18.2)
silhouette           0.78    Yeezy-Boost (70.7)               Air-Max/Hyperdunk (9.5)
releaseMonth         0.72    April (104.8)                    September (11.4)
colorwayType         0.69    named/nickname (62.7)            no colorway (12.6)
releasedOnWeekend    0.58    weekend (56.2)                   weekday (23.5)
```

colorwayType full breakdown: named/nickname 62.7, descriptive/color-word
33.8, no colorway (base release) 12.6 — named colorways sell roughly 5x a
plain base release on average, though this is a noisy signal (Blue-Tint and
Cream-White are the two highest-selling sneakers in the whole dataset
despite reading as "descriptive").

releaseMonth full breakdown (mean totalItemsSold): Apr 104.8, Jun 68.3,
Dec 56.4, Feb 49.3, Nov 37.6, Jul 36.9, Oct 18.4, Mar 15.9, Aug 12.2, Sep 11.4
(Jan and May have no releases in this dataset).

## 4. Retail price is a weak predictor of volume on its own (EDA 5)

```
corr(retailPrice, totalItemsSold) = 0.140
```

A weak positive relationship — a higher retail price does not meaningfully
predict higher or lower resale volume by itself. Not a feature the agent
should lean on heavily when reasoning about a specific allocation.

## 5. historicalBrandRegionDemand is a genuinely strong standalone signal (EDA 6)

```
corr(historicalBrandRegionDemand, totalItemsSold), pooled       = 0.571
  within Yeezy                                                   = 0.542
  within Off-White                                                = 0.651
```

This is the leave-one-out brand+region average the model itself uses as a
feature (a sneaker's own sales never leak into its own value of this
column). The within-brand correlations rule out this just being an artifact
of brand's large effect on volume (section 3) — even inside a single brand,
this one column tracks actual demand moderately-to-strongly on its own.
Unlike retailPrice above, this is a feature the agent can genuinely lean on
when explaining an allocation for a brand/region pair with real history,
not just cite as one weak input among several.

## How the allocation agent should use this

1. Default split: take the model's predicted total demand for the SKU being
   allocated and distribute it across regions using the fixed share table in
   section 1, rather than trusting a per-region model prediction in isolation
   for a product with little or no history — per-region predictions for an
   unseen SKU are individually noisier than this pooled, product-invariant
   curve.

2. Brand / silhouette / colorwayType / releaseMonth / releasedOnWeekend are
   volume dials, not location dials (section 3). When explaining an
   allocation, cite these as reasons for a LARGER OR SMALLER TOTAL pool, not
   as a reason to send proportionally more of that pool to any specific
   region.

3. Only treat a per-region deviation from the fixed share curve as
   meaningful if it is large. Even the least product-invariant category
   observed (Air-Jordan) still correlates at 0.957 with the overall curve
   (section 2) — small deviations from the curve are more likely sampling
   noise in a 50-sneaker dataset than a genuine regional preference, and
   should not be over-explained.

4. This file gives static priors, not a reason for one specific prediction.
   Pair it with per-prediction feature attribution (e.g. SHAP on the trained
   XGBoost model, `models/xgb_tweedie_new_sku.joblib`) to cite the top 1-2
   features actually driving a given region's predicted number. Weight
   historicalBrandRegionDemand (section 5) more heavily than retailPrice
   (section 4) when both show up as contributors — one is a genuinely strong
   signal, the other is weak.

5. Respect `region_warehouse_capacity` after computing the desired split. If
   demand-based allocation for a region would exceed its capacity, say so
   explicitly in the reasoning ("California would receive more under demand
   alone, but warehouse capacity caps it at X") rather than silently
   reallocating the difference.

## Caveat

All numbers above come from one dataset: ~99k transactions, 2017-2019, 2
brands (Yeezy, Off-White), 9 silhouettes. The regional concentration pattern
is consistent across every product observed WITHIN this data, which is
enough to trust as a working prior, but it is one dataset's snapshot of
resale demand, not an independently validated regional market model.
