import pytest
import numpy as np
import pandas as pd
from datetime import datetime
from app.models.battery import Battery
from app.models.optimizer import BatteryOptimizer
from app.utils.data_generator import generate_synthetic_data

def test_optimizer_initialization():
    """Test optimizer initialization."""
    optimizer = BatteryOptimizer()
    assert optimizer.model is not None
    assert optimizer.scaler is None

def test_feature_preparation():
    """Test feature preparation for the neural network."""
    optimizer = BatteryOptimizer()
    
    # Create sample data
    start_time = datetime(2024, 1, 1)
    data = generate_synthetic_data(
        start_time=start_time,
        horizon_hours=24,
        interval_minutes=5
    )
    
    battery_state = {
        'soc': 0.5,
        'capacity_mwh': 100.0,
        'max_power_mw': 20.0
    }
    
    # Test feature preparation
    features = optimizer._prepare_features(
        prices=data['prices'],
        forecasts=data['forecasts'],
        battery_state=battery_state
    )
    
    assert features.shape[1] == 4  # Should have 4 features
    assert not np.any(np.isnan(features))  # No NaN values
    assert not np.any(np.isinf(features))  # No infinite values

def test_optimization_run():
    """Test full optimization run."""
    optimizer = BatteryOptimizer()
    battery = Battery(
        capacity_mwh=100.0,
        max_power_mw=20.0,
        efficiency=0.92,
        initial_soc=0.5
    )
    
    # Generate test data
    start_time = datetime(2024, 1, 1)
    data = generate_synthetic_data(
        start_time=start_time,
        horizon_hours=24,
        interval_minutes=5
    )
    
    # Run optimization
    schedule = optimizer.optimize(
        battery=battery,
        prices=data['prices'],
        forecasts=data['forecasts']
    )
    
    # Check schedule structure
    assert isinstance(schedule, pd.DataFrame)
    assert 'power_mw' in schedule.columns
    assert 'soc' in schedule.columns
    assert 'price' in schedule.columns
    assert 'profit' in schedule.columns
    
    # Check schedule values
    assert len(schedule) == len(data['prices'])
    assert all(-battery.max_power_mw <= p <= battery.max_power_mw 
              for p in schedule['power_mw'])
    assert all(battery.min_soc <= s <= battery.max_soc 
              for s in schedule['soc'])

def test_optimizer_constraints():
    """Test that optimizer respects battery constraints."""
    optimizer = BatteryOptimizer()
    battery = Battery(
        capacity_mwh=100.0,
        max_power_mw=20.0,
        efficiency=0.92,
        initial_soc=0.1  # Start at minimum SOC
    )
    
    # Generate test data with high prices at start
    start_time = datetime(2024, 1, 1)
    data = generate_synthetic_data(
        start_time=start_time,
        horizon_hours=24,
        interval_minutes=5
    )
    
    # Artificially set high prices at start
    data['prices'].iloc[0:12] = 1000.0
    
    # Run optimization
    schedule = optimizer.optimize(
        battery=battery,
        prices=data['prices'],
        forecasts=data['forecasts']
    )
    
    # Check that battery doesn't discharge when SOC is at minimum
    assert schedule['power_mw'].iloc[0] <= 0
    assert schedule['soc'].iloc[0] >= battery.min_soc

def test_optimizer_profit_calculation():
    """Test that profit calculations are correct."""
    optimizer = BatteryOptimizer()
    battery = Battery(
        capacity_mwh=100.0,
        max_power_mw=20.0,
        efficiency=1.0,  # Perfect efficiency for easier calculation
        initial_soc=0.5
    )
    
    # Create simple price series
    start_time = datetime(2024, 1, 1)
    periods = 12  # 1 hour of 5-minute intervals
    index = pd.date_range(start=start_time, periods=periods, freq='5min')
    prices = pd.Series(50.0, index=index)  # Constant price
    
    # Create minimal forecasts
    forecasts = {'solar': pd.Series(0.5, index=index)}
    
    # Run optimization
    schedule = optimizer.optimize(
        battery=battery,
        prices=prices,
        forecasts=forecasts
    )
    
    # Calculate expected profit for each interval
    for _, row in schedule.iterrows():
        power = row['power_mw']
        price = row['price']
        expected_profit = -power * price * (5/60)  # Negative because we pay when charging
        assert np.isclose(row['profit'], expected_profit, rtol=1e-10) 