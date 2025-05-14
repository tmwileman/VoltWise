import pytest
import numpy as np
from app.models.battery import Battery

def test_battery_initialization():
    """Test battery initialization with default values."""
    battery = Battery(
        capacity_mwh=100.0,
        max_power_mw=20.0,
        efficiency=0.92,
        initial_soc=0.5
    )
    
    assert battery.capacity_mwh == 100.0
    assert battery.max_power_mw == 20.0
    assert battery.efficiency == 0.92
    assert battery.current_soc == 0.5
    assert np.isclose(battery.charge_efficiency, np.sqrt(0.92))
    assert np.isclose(battery.discharge_efficiency, np.sqrt(0.92))

def test_battery_power_limits():
    """Test battery power limits based on SOC."""
    battery = Battery(
        capacity_mwh=100.0,
        max_power_mw=20.0,
        efficiency=1.0,  # Perfect efficiency for easier calculation
        initial_soc=0.5
    )
    
    # Test discharge power limit
    max_discharge = battery.get_available_power('discharge')
    assert max_discharge <= 20.0  # Should not exceed max power
    
    # Test charge power limit
    max_charge = battery.get_available_power('charge')
    assert max_charge <= 20.0  # Should not exceed max power
    
    # Test when battery is empty
    battery.current_soc = battery.min_soc
    assert battery.get_available_power('discharge') == 0.0
    
    # Test when battery is full
    battery.current_soc = battery.max_soc
    assert battery.get_available_power('charge') == 0.0

def test_battery_step():
    """Test battery state updates during charge/discharge."""
    battery = Battery(
        capacity_mwh=100.0,
        max_power_mw=20.0,
        efficiency=0.92,
        initial_soc=0.5
    )
    
    # Test charging
    initial_soc = battery.current_soc
    result = battery.step(-10.0, interval_hours=1.0)  # Charge at 10 MW for 1 hour
    assert battery.current_soc > initial_soc
    assert result['power_mw'] == -10.0
    assert result['energy_change_mwh'] == -10.0
    
    # Test discharging
    initial_soc = battery.current_soc
    result = battery.step(10.0, interval_hours=1.0)  # Discharge at 10 MW for 1 hour
    assert battery.current_soc < initial_soc
    assert result['power_mw'] == 10.0
    assert result['energy_change_mwh'] == 10.0

def test_battery_constraints():
    """Test that battery respects SOC constraints."""
    battery = Battery(
        capacity_mwh=100.0,
        max_power_mw=20.0,
        efficiency=1.0,
        initial_soc=0.5
    )
    
    # Try to discharge beyond minimum SOC
    while battery.current_soc > battery.min_soc:
        battery.step(20.0, interval_hours=1.0)
    
    # One more discharge attempt
    battery.step(20.0, interval_hours=1.0)
    assert battery.current_soc >= battery.min_soc
    
    # Try to charge beyond maximum SOC
    while battery.current_soc < battery.max_soc:
        battery.step(-20.0, interval_hours=1.0)
    
    # One more charge attempt
    battery.step(-20.0, interval_hours=1.0)
    assert battery.current_soc <= battery.max_soc

def test_battery_reset():
    """Test battery reset functionality."""
    battery = Battery(
        capacity_mwh=100.0,
        max_power_mw=20.0,
        efficiency=0.92,
        initial_soc=0.5
    )
    
    # Change state
    battery.step(10.0, interval_hours=1.0)
    assert battery.current_soc != 0.5
    
    # Reset to default
    battery.reset()
    assert battery.current_soc == 0.5
    
    # Reset to specific value
    battery.reset(soc=0.7)
    assert battery.current_soc == 0.7 