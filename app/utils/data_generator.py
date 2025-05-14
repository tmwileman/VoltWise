import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_price_data(start_time, periods, interval_minutes=5, scenario='normal'):
    """
    Generate synthetic electricity price data.
    
    Args:
        start_time (datetime): Start time for the data
        periods (int): Number of periods to generate
        interval_minutes (int): Time interval in minutes
        scenario (str): Type of price scenario ('normal', 'volatile', 'high_peaks')
        
    Returns:
        pd.Series: Time series of prices
    """
    # Base parameters
    base_price = 50  # Base price in $/MWh
    
    # Time-based components
    time_index = pd.date_range(
        start=start_time,
        periods=periods,
        freq=f'{interval_minutes}min'
    )
    
    # Hour of day effect (peak during morning and evening)
    hours = time_index.hour
    hour_effect = (
        10 * np.sin(2 * np.pi * (hours - 8) / 24) +  # Morning peak
        15 * np.sin(2 * np.pi * (hours - 18) / 24)   # Evening peak
    )
    
    # Random component
    if scenario == 'normal':
        noise = np.random.normal(0, 5, periods)
    elif scenario == 'volatile':
        noise = np.random.normal(0, 15, periods)
    elif scenario == 'high_peaks':
        noise = np.random.normal(0, 5, periods)
        # Add occasional price spikes
        spike_prob = 0.02
        spikes = np.random.choice(
            [0, 1],
            size=periods,
            p=[1-spike_prob, spike_prob]
        )
        noise += spikes * np.random.uniform(50, 100, periods)
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
        
    # Combine components
    prices = base_price + hour_effect + noise
    
    # Ensure no negative prices
    prices = np.maximum(prices, 0)
    
    return pd.Series(prices, index=time_index)

def generate_solar_forecast(start_time, periods, interval_minutes=5):
    """
    Generate synthetic solar generation forecast.
    
    Args:
        start_time (datetime): Start time for the data
        periods (int): Number of periods to generate
        interval_minutes (int): Time interval in minutes
        
    Returns:
        pd.Series: Time series of solar generation forecasts (0-1 scale)
    """
    time_index = pd.date_range(
        start=start_time,
        periods=periods,
        freq=f'{interval_minutes}min'
    )
    
    # Solar generation follows a bell curve during daylight hours
    hours = time_index.hour + time_index.minute / 60
    
    # Center peak at noon (hour 12)
    solar = np.maximum(0, np.sin(np.pi * (hours - 6) / 12))
    
    # Add some noise to represent cloud cover, etc.
    noise = np.random.normal(0, 0.1, periods)
    solar = np.clip(solar + noise, 0, 1)
    
    return pd.Series(solar, index=time_index)

def generate_synthetic_data(start_time, horizon_hours=24, interval_minutes=5):
    """
    Generate complete synthetic dataset including prices and forecasts.
    
    Args:
        start_time (datetime): Start time for the data
        horizon_hours (int): Number of hours to generate data for
        interval_minutes (int): Time interval in minutes
        
    Returns:
        dict: Dictionary containing price and forecast data
    """
    periods = int(horizon_hours * 60 / interval_minutes)
    
    # Generate price data
    prices = generate_price_data(
        start_time=start_time,
        periods=periods,
        interval_minutes=interval_minutes
    )
    
    # Generate solar forecast
    solar = generate_solar_forecast(
        start_time=start_time,
        periods=periods,
        interval_minutes=interval_minutes
    )
    
    # Package data
    data = {
        'prices': prices,
        'forecasts': {
            'solar': solar
        },
        'metadata': {
            'start_time': start_time,
            'horizon_hours': horizon_hours,
            'interval_minutes': interval_minutes
        }
    }
    
    return data

def get_sample_day(scenario='normal'):
    """
    Get a sample day of data for demonstration.
    
    Args:
        scenario (str): Type of price scenario
        
    Returns:
        dict: Sample dataset
    """
    # Use a fixed start time for reproducibility
    start_time = datetime(2024, 1, 1, 0, 0)
    
    return generate_synthetic_data(
        start_time=start_time,
        horizon_hours=24,
        interval_minutes=5,
        scenario=scenario
    ) 