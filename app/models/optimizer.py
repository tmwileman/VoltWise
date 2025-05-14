import numpy as np
import pandas as pd
import logging

# Configure logging
logger = logging.getLogger(__name__)

class BatteryOptimizer:
    """
    Rule-based battery dispatch optimizer.
    """
    
    def __init__(self):
        """Initialize the optimizer."""
        logger.info("Initializing BatteryOptimizer")
        
    def optimize(self, battery, prices, forecasts):
        """
        Generate optimized dispatch schedule using a simple price-based strategy.
        
        Args:
            battery (Battery): Battery instance
            prices (pd.Series): Price data
            forecasts (dict): Forecast data
            
        Returns:
            pd.DataFrame: Optimized dispatch schedule
        """
        logger.info("Starting optimization")
        try:
            # Initialize results storage
            results = []
            current_time = prices.index[0]
            end_time = prices.index[-1]
            
            # Calculate price thresholds for charging/discharging
            price_mean = prices.mean()
            price_std = prices.std()
            charge_threshold = price_mean - 0.5 * price_std
            discharge_threshold = price_mean + 0.5 * price_std
            
            # Reset battery to initial state
            battery.reset()
            
            while current_time <= end_time:
                # Get current state
                state = battery.get_state()
                price = prices[current_time]
                solar = forecasts['solar'][current_time]
                
                # Simple rule-based strategy:
                # 1. If price is low and battery not full -> charge
                # 2. If price is high and battery not empty -> discharge
                # 3. Otherwise -> idle
                
                if price < charge_threshold and state['soc'] < 0.95:
                    # Charge at max rate
                    max_charge = battery.get_available_power('charge')
                    power = -max_charge  # Negative for charging
                elif price > discharge_threshold and state['soc'] > 0.05:
                    # Discharge at max rate
                    max_discharge = battery.get_available_power('discharge')
                    power = max_discharge
                else:
                    # Idle
                    power = 0
                    
                # Apply the action and get updated state
                updated = battery.step(power, interval_hours=5/60)
                
                # Calculate profit for this interval
                profit = -power * price * (5/60)  # Negative because we pay when charging
                
                # Store results
                results.append({
                    'timestamp': current_time,
                    'power_mw': power,
                    'soc': updated['soc'],
                    'price': price,
                    'profit': profit
                })
                
                # Move to next time step
                current_time = current_time + pd.Timedelta(minutes=5)
            
            logger.info("Optimization completed successfully")
            
            # Convert results to DataFrame
            schedule = pd.DataFrame(results)
            schedule.set_index('timestamp', inplace=True)
            
            # Add energy columns
            schedule['energy_charged'] = np.where(schedule['power_mw'] < 0,
                                                -schedule['power_mw'] * (5/60),
                                                0)
            schedule['energy_discharged'] = np.where(schedule['power_mw'] > 0,
                                                   schedule['power_mw'] * (5/60),
                                                   0)
            
            return schedule
            
        except Exception as e:
            logger.error(f"Error in optimize: {str(e)}")
            raise 