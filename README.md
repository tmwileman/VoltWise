# VoltWise - Battery Energy Storage System (BESS) Optimization

VoltWise is an intelligent battery dispatch optimization tool designed to help Battery Energy Storage System (BESS) operators maximize economic returns while maintaining battery health. The application uses AI to provide optimal charging and discharging recommendations based on market conditions and battery state.

## Features

- 5-minute interval dispatch recommendations
- Real-time price-based optimization
- Battery state of charge (SoC) tracking
- Interactive visualization of dispatch schedules
- Economic performance metrics
- Battery health consideration

## Technical Stack

- Backend: Python with Flask
- Frontend: React
- AI/ML: TensorFlow/Keras
- Data Processing: NumPy, Pandas
- Visualization: Plotly

## Setup

1. Create a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the development server:
```bash
python app/main.py
```

4. Access the web interface at `http://localhost:5001`

## Project Structure

```
VoltWise/
├── app/
│   ├── api/          # API endpoints
│   ├── models/       # Neural network and battery models
│   ├── static/       # Frontend assets
│   ├── templates/    # HTML templates
│   ├── utils/        # Utility functions
│   ├── __init__.py
│   └── main.py       # Application entry point
├── data/            # Synthetic data and training data
├── models/          # Saved model weights
├── tests/           # Unit tests
├── docs/            # Documentation
├── requirements.txt # Python dependencies
└── README.md
```

## Development

This is an MVP (Minimum Viable Product) focused on demonstrating the core optimization logic and user interface. The system uses synthetic data to simulate market conditions and battery behavior.

## License

Copyright (c) 2024 VoltWise. All rights reserved.
