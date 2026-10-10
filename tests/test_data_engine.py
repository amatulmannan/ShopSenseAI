
import csv

import pytest

from data_engine import (
    anomaly_summary,
    get_reorder_candidates,
    load_products,
    load_sales,
    sales_summary,
    validate_product_references,
)


def write_csv(path, headers, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)


def test_sample_sales_hand_calculated():
    loaded = load_sales("sample_sales.csv")
    assert loaded["ok"] is True
    assert len(loaded["records"]) == 8

    summary = sales_summary(
        loaded["records"], "2026-10-01", "2026-10-04"
    )

    assert summary["revenue"] == pytest.approx(1260.00)
    assert summary["cost_of_goods_sold"] == pytest.approx(870.00)
    assert summary["gross_profit"] == pytest.approx(390.00)
    assert summary["units_sold"] == 22


def test_date_range_is_inclusive():
    records = load_sales("sample_sales.csv")["records"]
    result = sales_summary(records, "2026-10-01", "2026-10-01")

    assert result["revenue"] == pytest.approx(370.00)
    assert result["units_sold"] == 7


def test_missing_required_columns(tmp_path):
    path = tmp_path / "bad.csv"
    write_csv(path, ["sale_id", "date"], [["S1", "2026-10-01"]])

    result = load_sales(path)

    assert not result["ok"]
    assert any("Missing required columns" in e["message"]
               for e in result["errors"])


def test_invalid_date_and_negative_quantity(tmp_path):
    path = tmp_path / "invalid.csv"
    write_csv(path,
              ["sale_id", "date", "product_id", "quantity_sold",
               "unit_price", "unit_cost"],
              [["S1", "not-a-date", "P001", 2, 110, 80],
               ["S2", "2026-10-01", "P001", -1, 110, 80]])

    result = load_sales(path)

    assert not result["ok"]
    assert result["records"] == []
    assert len(result["errors"]) >= 2


def test_duplicate_sale_id_is_reported(tmp_path):
    path = tmp_path / "duplicates.csv"
    write_csv(path,
              ["sale_id", "date", "product_id", "quantity_sold",
               "unit_price", "unit_cost"],
              [["S1", "2026-10-01", "P001", 1, 110, 80],
               ["S1", "2026-10-02", "P001", 2, 110, 80]])

    result = load_sales(path)

    assert not result["ok"]
    assert len(result["records"]) == 1
    assert any("Duplicate sale_id" in e["message"]
               for e in result["errors"])


def test_missing_unit_cost_is_reported(tmp_path):
    path = tmp_path / "missing_cost.csv"
    write_csv(path,
              ["sale_id", "date", "product_id", "quantity_sold",
               "unit_price", "unit_cost"],
              [["S1", "2026-10-01", "P001", 2, 110, ""]])

    loaded = load_sales(path)
    assert not loaded["ok"]
    assert loaded["records"] == []

    summary = sales_summary(
        [{
            "sale_id": "S1",
            "date": "2026-10-01",
            "product_id": "P001",
            "quantity_sold": 2,
            "unit_price": 110,
            "unit_cost": None,
        }],
        "2026-10-01", "2026-10-01",
    )

    assert summary["revenue"] == pytest.approx(220)
    assert summary["cost_of_goods_sold"] is None
    assert summary["gross_profit"] is None


def test_empty_file_is_rejected(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")

    result = load_sales(path)
    assert not result["ok"]
    assert result["errors"]


def test_unsupported_format_is_rejected(tmp_path):
    path = tmp_path / "sales.json"
    path.write_text("{}", encoding="utf-8")

    result = load_sales(path)
    assert not result["ok"]
    assert result["errors"]


def test_product_reference_validation():
    sales = [
        {"sale_id": "S1", "product_id": "P999"},
        {"sale_id": "S2", "product_id": "P001"},
    ]
    products = [{"product_id": "P001"}]

    result = validate_product_references(sales, products)

    assert not result["ok"]
    assert len(result["errors"]) == 1
    assert result["errors"][0]["product_id"] == "P999"


def test_product_csv_loads():
    result = load_products("sample_products.csv")

    assert result["ok"] is True
    assert len(result["records"]) == 4


def test_reorder_formula_and_missing_demand():
    products = [
        {"product_id": "P1", "name": "Notebook",
         "quantity": 12, "reorder_level": 5},
        {"product_id": "P2", "name": "Pen",
         "quantity": 8, "reorder_level": 10},
    ]

    result = get_reorder_candidates(
        products,
        average_daily_sales={"P1": 2, "P2": 3},
        lead_time_days=7,
        safety_days=3,
    )

    notebook = next(x for x in result if x["product_id"] == "P1")
    pen = next(x for x in result if x["product_id"] == "P2")

    assert notebook["target_stock"] == 20
    assert notebook["suggested_reorder_quantity"] == 8
    assert pen["target_stock"] == 30
    assert pen["suggested_reorder_quantity"] == 22
    assert notebook["is_estimate"] is True


def test_missing_daily_demand_is_not_guessed():
    products = [
        {"product_id": "P1", "name": "Notebook",
         "quantity": 4, "reorder_level": 5}
    ]

    result = get_reorder_candidates(products)

    assert len(result) == 1
    assert result[0]["suggested_reorder_quantity"] is None
    assert result[0]["warnings"]


def test_invalid_date_range():
    result = sales_summary([], "2026-10-10", "2026-10-01")

    assert not result["ok"]
    assert result["warnings"]


def test_anomalies_are_not_called_fraud():
    result = anomaly_summary([
        {"sale_id": "S1", "quantity_sold": 1, "unit_price": 10},
        {"sale_id": "S1", "quantity_sold": 1, "unit_price": 10},
    ])

    assert any(
        item["type"] == "duplicate_sale_id"
        for item in result["anomalies"]
    )
    assert all(
        "fraud" not in item["message"].lower()
        for item in result["anomalies"]
    )
