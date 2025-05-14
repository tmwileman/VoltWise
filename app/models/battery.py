import numpy as np

class Battery:
    """
    Battery Energy Storage System (BESS) model.
    Handles battery state, constraints, and state updates.
    """
    
    def __init__(self, capacity_mwh, max_power_mw, efficiency, initial_soc=0.5):
        """
        Initialize battery parameters.
        
        Args:
            capacity_mwh (float): Battery capacity in MWh
            max_power_mw (float): Maximum charge/discharge power in MW
            efficiency (float): Round-trip efficiency (0-1)
            initial_soc (float): Initial state of charge (0-1)
        """
        self.capacity_mwh = capacity_mwh
        self.max_power_mw = max_power_mw
        self.efficiency = efficiency
        self.current_soc = initial_soc
        
        # Derived parameters
        self.charge_efficiency = np.sqrt(efficiency)  # Split round-trip efficiency
        self.discharge_efficiency = np.sqrt(efficiency)
        
        # Operational limits
        self.min_soc = 0.1  # Don't discharge below 10%
        self.max_soc = 0.9  # Don't charge above 90%
        
    def get_available_power(self, action='discharge'):
        """
        Calculate available power for charge or discharge.
        
        Args:
            action (str): Either 'charge' or 'discharge'
            
        Returns:
            float: Maximum power available for the action in MW
        """
        if action == 'discharge':
            # How much can we discharge?
            energy_available = (self.current_soc - self.min_soc) * self.capacity_mwh
            power_from_energy = energy_available * 12  # Convert MWh to MW (5-min basis)
            return min(power_from_energy * self.discharge_efficiency, self.max_power_mw)
            
        elif action == 'charge':
            # How much can we charge?
            energy_headroom = (self.max_soc - self.current_soc) * self.capacity_mwh
            power_from_energy = energy_headroom * 12  # Convert MWh to MW (5-min basis)
            return min(power_from_energy / self.charge_efficiency, self.max_power_mw)
            
        else:
            raise ValueError(f"Unknown action: {action}")
            
    def step(self, power_mw, interval_hours=1/12):
        """
        Update battery state based on charge/discharge power.
        
        Args:
            power_mw (float): Power in MW (positive for discharge, negative for charge)
            interval_hours (float): Time interval in hours (default 5 minutes = 1/12 hour)
            
        Returns:
            dict: Updated battery state information
        """
        if power_mw > 0:  # Discharging
            # Apply discharge efficiency
            energy_out = power_mw * interval_hours
            energy_from_battery = energy_out / self.discharge_efficiency
            
            # Update SOC
            self.current_soc -= energy_from_battery / self.capacity_mwh
            
        else:  # Charging (power_mw is negative)
            # Apply charge efficiency
            energy_in = -power_mw * interval_hours  # Make positive for charging
            energy_to_battery = energy_in * self.charge_efficiency
            
            # Update SOC
            self.current_soc += energy_to_battery / self.capacity_mwh
            
        # Ensure SOC stays within bounds
        self.current_soc = np.clip(self.current_soc, self.min_soc, self.max_soc)
        
        return {
            'soc': self.current_soc,
            'energy_change_mwh': power_mw * interval_hours,
            'power_mw': power_mw
        }
        
    def reset(self, soc=None):
        """
        Reset battery to initial or specified state.
        
        Args:
            soc (float, optional): State of charge to reset to. If None, uses initial_soc
        """
        if soc is not None:
            self.current_soc = np.clip(soc, self.min_soc, self.max_soc)
        else:
            self.current_soc = 0.5  # Default to 50%
            
    def get_state(self):
        """
        Get current battery state.
        
        Returns:
            dict: Current battery state information
        """
        return {
            'soc': self.current_soc,
            'capacity_mwh': self.capacity_mwh,
            'max_power_mw': self.max_power_mw,
            'efficiency': self.efficiency,
            'available_charge_mw': self.get_available_power('charge'),
            'available_discharge_mw': self.get_available_power('discharge')
        } 