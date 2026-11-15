# Coffee Shop Daily Operations: Data Codebook

## Source
Point-of-sale system and local weather service records for a single-location
coffee shop. Data covers 2 years of daily operations from 2024-07-01 to 2026-06-30.

## File: coffee_shop_daily_operations.csv

| Field | Type | Units | Description |
|-------|------|-------|-------------|
| date | date | YYYY-MM-DD | Calendar date |
| day_of_week | string | — | Day name (Monday–Sunday) |
| is_weekend | boolean | — | True for Saturday and Sunday |
| weather_category | string | — | sunny, cloudy, rainy, or extreme |
| customer_count | integer | customers | Number of customers served |
| avg_transaction_value | float | USD | Mean transaction amount for the day |
| daily_revenue | float | USD | customer_count × avg_transaction_value |
| operating_costs | float | USD | Fixed ($350) + variable ($2.00/customer) |
| daily_profit | float | USD | daily_revenue − operating_costs |

## Known Data Quality Issues

1. **2025-01-04**: Power outage closed the shop for most of the day.
   Customer count is abnormally low (~8). Consider removing this record
   before fitting distributions.

2. **2025-08-17 and 2026-02-10**: Equipment failures caused partial-day
   closures. Customer counts are roughly 30–50% of normal. Analyst judgment
   required on whether to remove, segment, or retain these records.

3. **Seasonal patterns**: Customer traffic varies by season (±3–4% from
   baseline). Consider segmenting by season or including seasonal adjustments
   when fitting distributions.

4. **High-revenue outliers**: A small number of days show unusually high
   transaction values. IQR-based outlier detection will flag these along
   with the equipment/outage days.

## File: weather_reference.csv

Lookup table with four weather categories, their historical frequencies,
customer impact descriptions, and plain-language definitions.

| Category | Frequency | Customer Impact | Description |
|----------|-----------|-----------------|-------------|
| sunny | ~41% | Baseline | Clear skies, comfortable temperature |
| cloudy | ~29% | ~4% reduction | Overcast but dry, mild conditions |
| rainy | ~23% | ~10% reduction | Rain or steady drizzle throughout the day |
| extreme | ~7% | ~22% reduction | Severe weather: heavy storms, ice, extreme heat/cold |

## Break-Even Threshold

Daily break-even revenue is approximately $630, based on fixed costs of $350
and variable costs of $2.00 per customer at typical traffic levels. About 10%
of observed days fall below this threshold, primarily on extreme weather days
and Mondays during winter.

## Summary Statistics (Full Dataset)

| Metric | Value |
|--------|-------|
| Mean daily revenue | ~$1,010 |
| Median daily revenue | ~$958 |
| P5 | ~$576 |
| P95 | ~$1,593 |
| Mean weekday customers | ~136 |
| Mean weekend customers | ~167 |
| Mean transaction value | ~$6.99 |
