"""Canonical CSV schemas; money values are currency-neutral unless confirmed by user."""
SALES_REQUIRED = ("sale_id", "date", "product_id", "quantity_sold", "unit_price")
SALES_OPTIONAL = ("unit_cost",)
PRODUCTS_REQUIRED = ("product_id", "name", "quantity", "reorder_level")
PRODUCTS_OPTIONAL = ("unit_cost", "selling_price")
