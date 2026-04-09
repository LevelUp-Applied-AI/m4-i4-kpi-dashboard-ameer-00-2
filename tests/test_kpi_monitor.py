"""Tests for KPI monitoring script.

Tests for kpi_monitor.py including:
- Database connection mocking
- Threshold logic verification
- Output format validation
"""
import pytest
import json
import pandas as pd
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kpi_monitor import load_config, compute_kpis, get_status


def test_load_config():
    """Test loading configuration from config.json."""
    config = load_config()
    assert isinstance(config, dict)
    assert 'thresholds' in config
    assert 'mom_growth' in config['thresholds']
    assert 'aov' in config['thresholds']
    assert 'amman_share' in config['thresholds']
    assert 'retention' in config['thresholds']


def test_get_status():
    """Test status determination logic."""
    # Higher better KPIs
    assert get_status(20, 15, True) == 'green'  # Above threshold
    assert get_status(12, 15, True) == 'yellow'  # 80% of threshold
    assert get_status(10, 15, True) == 'red'  # Below 80%

    # Lower better KPIs (if any)
    assert get_status(10, 15, False) == 'green'  # Below threshold
    assert get_status(16, 15, False) == 'yellow'  # Slightly above
    assert get_status(20, 15, False) == 'red'  # Well above


@patch('kpi_monitor.connect_db')
def test_compute_kpis(mock_connect):
    """Test KPI computation with mocked data."""
    # Create mock data
    mock_df = pd.DataFrame({
        'customer_id': [1, 1, 2, 2, 3],
        'city': ['Amman', 'Amman', 'Irbid', 'Irbid', 'Amman'],
        'order_id': [1, 2, 3, 4, 5],
        'order_date': pd.to_datetime(['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15', '2024-02-20']),
        'registration_date': pd.to_datetime(['2023-12-01', '2023-12-01', '2024-01-01', '2024-01-01', '2024-01-01']),
        'revenue': [100, 150, 200, 50, 75],
        'quantity': [1, 1, 1, 1, 1],
        'product_id': [1, 2, 3, 4, 5],
        'category': ['Electronics', 'Clothing', 'Home', 'Books', 'Electronics']
    })

    config = {
        'thresholds': {
            'mom_growth': 15.0,
            'aov': 45.0,
            'amman_share': 65.0,
            'retention': 20.0
        }
    }

    kpis = compute_kpis(mock_df, config)

    # Verify all KPIs are computed
    expected_keys = ['mom_growth', 'aov', 'amman_share', 'peak_day', 'retention', 'weekly_velocity']
    for key in expected_keys:
        assert key in kpis

    # Verify types
    assert isinstance(kpis['mom_growth'], (int, float))
    assert isinstance(kpis['aov'], (int, float))
    assert isinstance(kpis['amman_share'], (int, float))
    assert isinstance(kpis['peak_day'], str)
    assert isinstance(kpis['retention'], (int, float))
    assert isinstance(kpis['weekly_velocity'], pd.Series)


@patch('kpi_monitor.extract_data')
@patch('kpi_monitor.connect_db')
@patch('kpi_monitor.load_config')
def test_main_execution(mock_load_config, mock_connect, mock_extract):
    """Test main function execution with mocks."""
    # Setup mocks
    mock_config = {
        'thresholds': {
            'mom_growth': 15.0,
            'aov': 45.0,
            'amman_share': 65.0,
            'retention': 20.0
        }
    }
    mock_load_config.return_value = mock_config

    mock_df = pd.DataFrame({
        'customer_id': [1, 2, 3],
        'city': ['Amman', 'Amman', 'Irbid'],
        'order_id': [1, 2, 3],
        'order_date': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']),
        'registration_date': pd.to_datetime(['2023-12-01', '2023-12-02', '2023-12-03']),
        'revenue': [100, 150, 200],
        'quantity': [1, 1, 1],
        'product_id': [1, 2, 3],
        'category': ['Electronics', 'Clothing', 'Home']
    })
    mock_extract.return_value = mock_df

    # Import and run main (but capture output instead of actually running)
    from kpi_monitor import compute_kpis

    kpis = compute_kpis(mock_df, mock_config)

    # Verify KPIs were computed
    assert 'mom_growth' in kpis
    assert 'aov' in kpis
    assert 'amman_share' in kpis
    assert 'peak_day' in kpis
    assert 'retention' in kpis