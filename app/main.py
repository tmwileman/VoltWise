"""
Flask application for VoltWise
"""
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import our custom modules
try:
    from app.models.battery import Battery
    from app.models.optimizer import BatteryOptimizer
    from app.utils.data_generator import generate_synthetic_data
    logger.info("Successfully imported custom modules")
except Exception as e:
    logger.error(f"Error importing modules: {str(e)}")
    raise

# Initialize battery and optimizer
try:
    battery = Battery(
        capacity_mwh=100.0,  # 100 MWh battery
        max_power_mw=20.0,   # 20 MW max power
        efficiency=0.92,     # 92% round-trip efficiency
        initial_soc=0.5      # Start at 50% charge
    )
    optimizer = BatteryOptimizer()
    logger.info("Successfully initialized battery and optimizer")
except Exception as e:
    logger.error(f"Error initializing components: {str(e)}")
    raise

@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html')

@app.route('/api/optimize', methods=['POST'])
def optimize():
    """Generate and return an optimized dispatch schedule."""
    try:
        logger.info("Received optimization request")
        
        # Get parameters from request
        params = request.get_json()
        logger.debug(f"Request parameters: {params}")
        horizon_hours = params.get('horizon_hours', 24)
        start_time = datetime.now()
        
        # Generate synthetic data
        logger.info("Generating synthetic data")
        data = generate_synthetic_data(
            start_time=start_time,
            horizon_hours=horizon_hours,
            interval_minutes=5
        )
        logger.debug(f"Generated data shape - prices: {len(data['prices'])}, forecasts: {len(data['forecasts']['solar'])}")
        
        # Run optimization
        logger.info("Running optimization")
        schedule = optimizer.optimize(
            battery=battery,
            prices=data['prices'],
            forecasts=data['forecasts']
        )
        logger.debug(f"Optimization complete, schedule shape: {schedule.shape}")
        
        # Convert schedule to a format that can be JSON serialized
        schedule_dict = {
            'index': schedule.index.strftime('%Y-%m-%dT%H:%M:%S').tolist(),  # Convert timestamps to ISO strings
            'price': schedule['price'].astype(float).tolist(),  # Convert numpy types to native Python
            'power_mw': schedule['power_mw'].astype(float).tolist(),
            'soc': schedule['soc'].astype(float).tolist(),
            'profit': schedule['profit'].astype(float).tolist(),
            'energy_charged': schedule['energy_charged'].astype(float).tolist(),
            'energy_discharged': schedule['energy_discharged'].astype(float).tolist()
        }
        
        # Format response
        response = {
            'success': True,
            'schedule': schedule_dict,
            'metrics': {
                'total_profit': float(schedule['profit'].sum()),  # Convert numpy types to native Python
                'energy_charged': float(schedule['energy_charged'].sum()),
                'energy_discharged': float(schedule['energy_discharged'].sum()),
                'final_soc': float(schedule['soc'].iloc[-1])
            }
        }
        
        # Log response data for debugging
        logger.debug("Schedule data types:")
        for key, value in schedule_dict.items():
            logger.debug(f"{key}: {type(value)}, length: {len(value)}")
            if len(value) > 0:
                logger.debug(f"First value type: {type(value[0])}")
                logger.debug(f"First value: {value[0]}")
        
        logger.debug("Metrics data types:")
        for key, value in response['metrics'].items():
            logger.debug(f"{key}: {type(value)}")
            logger.debug(f"Value: {value}")
        
        logger.info("Successfully prepared response")
        
        # Convert to JSON string for inspection
        json_str = jsonify(response).get_data(as_text=True)
        logger.debug(f"JSON response preview (first 500 chars): {json_str[:500]}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in optimization endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/battery/status', methods=['GET'])
def battery_status():
    """Get current battery status."""
    try:
        status = {
            'capacity_mwh': battery.capacity_mwh,
            'max_power_mw': battery.max_power_mw,
            'current_soc': battery.current_soc,
            'efficiency': battery.efficiency
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error in battery status endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/battery/configure', methods=['POST'])
def configure_battery():
    """Update battery configuration."""
    try:
        logger.info("Received battery configuration request")
        params = request.get_json()
        logger.debug(f"Configuration parameters: {params}")
        
        battery.capacity_mwh = float(params.get('capacity_mwh', battery.capacity_mwh))
        battery.max_power_mw = float(params.get('max_power_mw', battery.max_power_mw))
        battery.current_soc = float(params.get('initial_soc', battery.current_soc))
        battery.efficiency = float(params.get('efficiency', battery.efficiency))
        
        logger.info("Successfully updated battery configuration")
        return jsonify({
            'success': True,
            'message': 'Battery configuration updated'
        })
        
    except Exception as e:
        logger.error(f"Error in battery configuration endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 