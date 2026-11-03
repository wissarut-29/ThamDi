import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent.sql_guard import SqlGuardError, check_sql

ALLOWED = {"customers", "orders"}


def test_plain_select_passes_and_gets_limit():
    result = check_sql("SELECT * FROM customers", ALLOWED)
    assert "LIMIT" in result.upper()


def test_existing_limit_not_duplicated():
    result = check_sql("SELECT * FROM customers LIMIT 5", ALLOWED)
    assert result.upper().count("LIMIT") == 1


def test_cte_select_passes_cte_name_not_treated_as_table():
    sql = "WITH recent AS (SELECT * FROM orders) SELECT * FROM recent"
    result = check_sql(sql, ALLOWED)
    assert result is not None


@pytest.mark.parametrize("op", ["UNION", "INTERSECT", "EXCEPT"])
def test_set_operations_pass(op):
    sql = f"SELECT customer_id FROM customers {op} SELECT customer_id FROM orders"
    result = check_sql(sql, ALLOWED)
    assert "LIMIT" in result.upper()


def test_cte_with_union_passes_and_cte_name_excluded():
    sql = (
        "WITH recent AS (SELECT * FROM orders) "
        "SELECT * FROM recent UNION SELECT * FROM customers"
    )
    result = check_sql(sql, ALLOWED)
    assert result is not None


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE customers",
        "DELETE FROM customers",
        "UPDATE customers SET name = 'x'",
        "INSERT INTO customers VALUES (1)",
        "ATTACH 'x.db' AS y",
        "PRAGMA show_tables",
        "COPY customers TO 'out.csv'",
    ],
)
def test_blocks_ddl_dml(sql):
    with pytest.raises(SqlGuardError):
        check_sql(sql, ALLOWED)


def test_blocks_dml_nested_inside_cte():
    sql = "WITH x AS (DELETE FROM customers RETURNING *) SELECT * FROM x"
    with pytest.raises(SqlGuardError):
        check_sql(sql, ALLOWED)


def test_blocks_multiple_statements_with_semicolon():
    with pytest.raises(SqlGuardError):
        check_sql("SELECT * FROM customers; DROP TABLE customers", ALLOWED)


def test_trailing_semicolon_alone_is_fine():
    result = check_sql("SELECT * FROM customers;", ALLOWED)
    assert result is not None


def test_blocks_table_outside_dataset():
    with pytest.raises(SqlGuardError):
        check_sql("SELECT * FROM other_dataset_table", ALLOWED)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM read_csv('x.csv')",
        "SELECT * FROM read_csv_auto('x.csv')",
        "SELECT * FROM read_parquet('y.parquet')",
        "SELECT * FROM glob('*.csv')",
    ],
)
def test_blocks_file_reading_functions(sql):
    with pytest.raises(SqlGuardError):
        check_sql(sql, ALLOWED)
