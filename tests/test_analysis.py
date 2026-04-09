"""Tests for the KPI dashboard analysis.

Write at least 3 tests:
1. test_extraction_returns_dataframes — extract_data returns a dict of DataFrames
2. test_kpi_computation_returns_expected_keys — compute_kpis returns a dict with your 5 KPI names
3. test_statistical_test_returns_pvalue — run_statistical_tests returns results with p-values
"""
import pytest
import pandas as pd
import sys
import os

# Add parent directory to path so we can import analysis
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import connect_db, extract_data, compute_kpis, run_statistical_tests  



def test_extraction_returns_dataframes():
    """Connect to the database, extract data, and verify the result is a dict of DataFrames."""
    # TODO: Call connect_db and extract_data, then assert the result is a dict
    #       with DataFrame values for each expected table
    engine = connect_db()
    data = extract_data(engine)
    assert isinstance(data, dict)
    
    expected_tables = ["customers", "products", "orders", "order_items"]
    for table in expected_tables:
        assert table in data 
        assert isinstance(data[table], pd.DataFrame)
        assert len(data[table]) > 0



def test_kpi_computation_returns_expected_keys():
    """Compute KPIs and verify the result contains all expected KPI names."""
    # TODO: Extract data, call compute_kpis, then assert the returned dict
    #       contains the keys matching your 5 KPI names
    engine = connect_db()
    data = extract_data(engine)
    kpis = compute_kpis(data)
    expected_kpi_names = [
        "Total Revenue",
        "Average Order Value", 
        "Customer Retention Rate", 
        "Monthly Active Users", 
        "Cohort Revenue Growth"]
    for kpi in expected_kpi_names:
        assert kpi in kpis, f"Missing KPI: {kpi}"


def test_statistical_test_returns_pvalue():
    """Run statistical tests and verify results include p-values."""
    # TODO: Extract data, call run_statistical_tests, then assert at least
    #       one result contains a numeric p-value between 0 and 1
    engine = connect_db()
    data = extract_data(engine)
    kpis = compute_kpis(data)
    stats_results = run_statistical_tests(kpis)

    assert"city_comparison" in stats_results
    p_val = stats_results["city_comparison"]["p_value"]
    assert isinstance(p_val, (float, int))
    assert 0 <= p_val <= 1

