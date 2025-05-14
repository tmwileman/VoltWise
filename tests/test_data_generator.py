import pytest
from datetime import datetime
import numpy as np
from app.utils.data_generator import (
    generate_price_data,
    generate_solar_forecast,
    generate_synthetic_data
)

def test_price_data_generation():
    """Test price data generation with different scenarios."""
    start_time = datetime(2024, 1, 1)
    periods = 288  # 24 hours at 5-minute intervals
    
    # Test normal scenario
    prices = generate_price_data(start_time, periods, scenario='normal')
    assert len(prices) == periods
    assert all(p >= 0 for p in prices)  # No negative prices
    assert prices.index[0] == start_time
    
    # Test volatile scenario
    volatile_prices = generate_price_data(start_time, periods, scenario='volatile')
    assert len(volatile_prices) == periods
    
    # Volatile prices should have higher standard deviation
    assert volatile_prices.std() > prices.std()
    
    # Test high peaks scenario
    peak_prices = generate_price_data(start_time, periods, scenario='high_peaks')
    assert len(peak_prices) == periods
    assert max(peak_prices) > max(prices)  # Should have higher peaks

def test_solar_forecast_generation():
    """Test solar generation forecast."""
    start_time = datetime(2024, 1, 1)
    periods = 288
    
    solar = generate_solar_forecast(start_time, periods)
    
    assert len(solar) == periods
    assert all(0 <= s <= 1 for s in solar)  # Values should be between 0 and 1
    
    # Check that solar output is zero at midnight
    midnight_value = solar[start_time]
    assert np.isclose(midnight_value, 0, atol=0.1)
    
    # Check that peak is around noon
    noon = datetime(2024, 1, 1, 12)
    noon_value = solar[noon]
    assert noon_value > 0.5  # Should be high at noon

def test_complete_synthetic_data():
    """Test complete synthetic dataset generation."""
    start_time = datetime(2024, 1, 1)
    
    data = generate_synthetic_data(
        start_time=start_time,
        horizon_hours=24,
        interval_minutes=5
    )
    
    # Check structure
    assert 'prices' in data
    assert 'forecasts' in data
    assert 'metadata' in data
    assert 'solar' in data['forecasts']
    
    # Check metadata
    assert data['metadata']['start_time'] == start_time
    assert data['metadata']['horizon_hours'] == 24
    assert data['metadata']['interval_minutes'] == 5
    
    # Check data lengths
    expected_periods = 24 * 12  # 24 hours * 12 5-minute intervals per hour
    assert len(data['prices']) == expected_periods
    assert len(data['forecasts']['solar']) == expected_periods
    
    # Check time alignment
    assert data['prices'].index[0] == start_time
    assert data['forecasts']['solar'].index[0] == start_time

def test_data_time_intervals():
    """Test different time intervals in data generation."""
    start_time = datetime(2024, 1, 1)
    
    # Test 15-minute intervals
    data_15min = generate_synthetic_data(
        start_time=start_time,
        horizon_hours=24,
        interval_minutes=15
    )
    
    assert len(data_15min['prices']) == 24 * 4  # 96 periods for 15-min intervals
    
    # Test hourly intervals
    data_60min = generate_synthetic_data(
        start_time=start_time,
        horizon_hours=24,
        interval_minutes=60
    )
    
    assert len(data_60min['prices']) == 24  # 24 periods for hourly intervals 