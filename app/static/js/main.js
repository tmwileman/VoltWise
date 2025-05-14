// Main JavaScript for VoltWise

document.addEventListener('DOMContentLoaded', function() {
    // Get form element
    const form = document.getElementById('batteryForm');
    
    // Initialize charts
    let priceChart = null;
    let powerChart = null;
    let socChart = null;
    
    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get form values
        const data = {
            capacity_mwh: parseFloat(document.getElementById('capacity').value),
            max_power_mw: parseFloat(document.getElementById('power').value),
            initial_soc: parseFloat(document.getElementById('soc').value) / 100,
            scenario: document.getElementById('scenario').value,
            horizon_hours: 24
        };
        
        // Disable form while processing
        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.innerHTML = 'Running...';
        
        // Update battery configuration
        fetch('/api/battery/configure', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text().then(text => {
                try {
                    console.log('Battery config response:', text);  // Log raw response
                    return JSON.parse(text);
                } catch (e) {
                    console.error('Error parsing battery config JSON:', text);
                    throw new Error('Invalid JSON response from server');
                }
            });
        })
        .then(configResult => {
            if (!configResult.success) {
                throw new Error(configResult.error || 'Failed to configure battery');
            }
            
            // Run optimization
            return fetch('/api/optimize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text().then(text => {
                try {
                    console.log('Optimization response:', text);  // Log raw response
                    const result = JSON.parse(text);
                    console.log('Parsed optimization result:', result);  // Log parsed result
                    return result;
                } catch (e) {
                    console.error('Error parsing optimization JSON:', text);
                    console.error('Parse error details:', e);
                    throw new Error('Invalid JSON response from server');
                }
            });
        })
        .then(result => {
            if (!result) {
                throw new Error('Empty response from server');
            }
            if (result.success) {
                console.log('Schedule data:', result.schedule);  // Log schedule data
                updateCharts(result.schedule);
                updateResults(result.metrics);
            } else {
                throw new Error(result.error || 'Optimization failed');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            const errorMessage = error.message || 'An error occurred while running the optimization.';
            // Show error in UI instead of using alert
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = `<div class="alert alert-danger">${errorMessage}</div>`;
        })
        .finally(() => {
            // Re-enable form
            submitButton.disabled = false;
            submitButton.innerHTML = 'Run Optimization';
        });
    });
    
    function updateCharts(schedule) {
        // Convert schedule data
        const timestamps = schedule.index;
        const prices = schedule.price;
        const power = schedule.power_mw;
        const soc = schedule.soc;
        
        // Price chart
        const priceTrace = {
            x: timestamps,
            y: prices,
            type: 'scatter',
            name: 'Price ($/MWh)',
            line: {color: '#2ecc71'}
        };
        
        const priceLayout = {
            title: 'Electricity Price',
            xaxis: {title: 'Time'},
            yaxis: {title: 'Price ($/MWh)'},
            height: 300,
            margin: {t: 30, b: 40, l: 60, r: 40}
        };
        
        Plotly.newPlot('priceChart', [priceTrace], priceLayout);
        
        // Power chart
        const powerTrace = {
            x: timestamps,
            y: power,
            type: 'bar',
            name: 'Power (MW)',
            marker: {
                color: power.map(p => p >= 0 ? '#e74c3c' : '#3498db')
            }
        };
        
        const powerLayout = {
            title: 'Battery Power',
            xaxis: {title: 'Time'},
            yaxis: {title: 'Power (MW)'},
            height: 300,
            margin: {t: 30, b: 40, l: 60, r: 40}
        };
        
        Plotly.newPlot('powerChart', [powerTrace], powerLayout);
        
        // SOC chart
        const socTrace = {
            x: timestamps,
            y: soc.map(s => s * 100),  // Convert to percentage
            type: 'scatter',
            name: 'State of Charge (%)',
            line: {color: '#9b59b6'}
        };
        
        const socLayout = {
            title: 'Battery State of Charge',
            xaxis: {title: 'Time'},
            yaxis: {
                title: 'SOC (%)',
                range: [0, 100]
            },
            height: 300,
            margin: {t: 30, b: 40, l: 60, r: 40}
        };
        
        Plotly.newPlot('socChart', [socTrace], socLayout);
    }
    
    function updateResults(metrics) {
        // Update results summary
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = `
            <p><strong>Total Profit:</strong> $${metrics.total_profit.toFixed(2)}</p>
            <p><strong>Energy Charged:</strong> ${metrics.energy_charged.toFixed(2)} MWh</p>
            <p><strong>Energy Discharged:</strong> ${metrics.energy_discharged.toFixed(2)} MWh</p>
            <p><strong>Final SoC:</strong> ${(metrics.final_soc * 100).toFixed(1)}%</p>
        `;
    }
}); 