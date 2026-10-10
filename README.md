
# ShopSense AI: Member 2 Data & Analytics

## Purpose

This module reads CSV sales and product records, validates input data,
calculates business summaries, and estimates possible stock reorder needs.

It is an educational prototype. It is not accounting, tax, investment,
or guaranteed demand-prediction advice.

## Files

- `data_engine.py`: CSV loaders, validation, summaries, reorder estimates,
  product-reference checks, and anomaly reporting.
- `sample_sales.csv`: fictional sales records.
- `sample_products.csv`: fictional product and inventory records.
- `tests/test_data_engine.py`: automated tests.

## Sales data dictionary

| Field | Meaning |
|---|---|
| sale_id | Unique sale identifier |
| date | Sale date in YYYY-MM-DD format |
| product_id | Product reference |
| quantity_sold | Positive whole number of units sold |
| unit_price | Non-negative selling price per unit |
| unit_cost | Non-negative cost per unit |

## Product data dictionary

| Field | Meaning |
|---|---|
| product_id | Unique product identifier |
| name | Product name |
| quantity | Current recorded stock, a non-negative whole number |
| unit_cost | Non-negative cost per unit |
| selling_price | Non-negative selling price |
| reorder_level | Non-negative stock threshold |

## Calculations

Revenue = sum(quantity_sold * unit_price)

COGS = sum(quantity_sold * unit_cost)

Gross profit = revenue - COGS

Gross profit is NOT net profit. Rent, wages, utilities, taxes, delivery,
returns, and other expenses are excluded unless separately recorded.

Money values are parsed using Python Decimal to avoid binary floating-point
arithmetic during calculations. Public summary totals are returned as floats
to preserve the shared dictionary interface.

## Validation policy

- Unsupported file formats are rejected.
- Missing required columns are reported as file-level errors.
- Invalid rows are excluded from valid records and reported with row details.
- Duplicate sale IDs: the first occurrence is retained; subsequent
  occurrences are rejected.
- Invalid dates must be corrected before a row is accepted.
- Sales quantities must be positive whole numbers.
- Product stock and reorder levels must be non-negative whole numbers.
- Missing unit_cost prevents a sale row from being accepted by load_sales.
- Unknown product references are checked using validate_product_references.
- Empty CSV files and unsupported formats are rejected.
- Valid rows may be returned alongside errors. Callers must inspect `ok`,
  `errors`, and `warnings`, not just `records`.

## Returns, discounts, tax, and dates

The shared schema does not contain return, discount, or tax fields.
These adjustments are not calculated or inferred.

Dates are inclusive calendar dates. No timestamps or time zones are used.
The start and end dates use YYYY-MM-DD format.

## Inventory assumptions

Product quantity is treated as the recorded stock snapshot. The module
does not subtract sales from stock automatically because the stock snapshot
may be before or after the sales period.

Reorder estimates use:

Target stock = ceil(average daily sales * (lead time days + safety days))

Suggested reorder quantity = max(0, target stock - current stock)

Average daily sales, supplier lead time, and safety days are assumptions.
Missing demand is disclosed rather than guessed. Suggestions are estimates,
not purchase orders, and do not modify inventory.

## Anomaly handling

Anomalies are possible data-quality issues, not proof of fraud.

## Run tests

```powershell
python -m pytest tests/test_data_engine.py -v
```

## Prototype safety

Use fictional data for initial testing. This module does not make purchases,
send messages, delete records, or automatically change inventory.

# ShopSense AI: Member 2 Data & Analytics

## Purpose
Read-only CSV validation, sales summaries, gross-profit calculations,
inventory reorder estimates, and basic data-anomaly reporting.

## Files
- `data_engine.py`: data loading, validation, calculations, reorder estimates.
- `sample_sales.csv`: fictional sales data.
- `sample_products.csv`: fictional product and stock data.
- `tests/test_data_engine.py`: automated tests.

## Calculations
- Revenue = quantity sold × selling price per unit
- COGS = quantity sold × cost per unit
- Gross profit = revenue − COGS

Gross profit is not net profit. Rent, wages, taxes, returns, and other
expenses are not included unless separately recorded.

## Inventory assumptions
- Product quantity is the recorded stock snapshot.
- Sales are not automatically subtracted from stock.
- Reorder estimates use average daily sales, lead time, and safety days.
- Missing demand is reported instead of guessed.
- Reorder suggestions do not create purchase orders or modify stock.

## Data validation
- CSV files must contain the required columns.
- Invalid rows and duplicate IDs are reported.
- Dates use `YYYY-MM-DD`.
- Sales quantities must be positive whole numbers.
- Stock and reorder levels must be non-negative whole numbers.
- Unknown product references can be checked with
  `validate_product_references()`.
- Anomalies are possible data-quality issues, not proof of fraud.

## Run tests
```powershell
python -m pytest tests/test_data_engine.py -v
```

## Safety
Use fictional data for testing. This module does not make purchases,
send customer messages, delete records, or automatically change inventory.
