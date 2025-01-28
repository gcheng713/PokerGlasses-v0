# PokerGlasses

A smart glasses application designed to assist poker players by providing real-time information and analysis during gameplay.

## Project Structure

```
pokerglasses/
├── core/                    # Core application logic
│   ├── game/               # Game state and poker logic
│   │   ├── cards.py        # Card recognition and handling
│   │   ├── hands.py        # Hand evaluation
│   │   └── odds.py         # Probability calculations
│   ├── vision/             # Computer vision components
│   │   ├── capture.py      # Camera input handling
│   │   ├── detector.py     # Card detection
│   │   └── calibration.py  # Camera calibration
│   └── hud/                # Heads-up display
│       ├── renderer.py     # Display rendering
│       ├── layouts.py      # UI layouts
│       └── themes.py       # Visual themes
├── ml/                     # Machine learning (optional)
│   ├── models/             # ML model definitions
│   ├── training/           # Training scripts
│   └── inference/          # Inference optimization
├── utils/                  # Utility functions
│   ├── config.py          # Configuration handling
│   ├── logger.py          # Logging setup
│   └── performance.py     # Performance monitoring
├── hardware/               # Hardware interfaces
│   ├── glasses.py         # Smart glasses drivers
│   └── controls.py        # Input handling
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── config/               # Configuration files
│   ├── default.yml      # Default settings
│   └── user.yml         # User settings
└── scripts/             # Utility scripts
    ├── setup.py         # Installation script
    └── deploy.py        # Deployment script
```

## Description

PokerGlasses is an innovative project that combines augmented reality (AR) technology with poker strategy assistance. The application runs on smart glasses and helps players by:
- Identifying cards on the table
- Calculating pot odds and equity
- Providing statistical information
- Suggesting optimal plays based on current game state

**Note:** This project is intended for practice and learning purposes only. Please check local regulations regarding the use of assistance devices during poker games.

## Features

- Real-time card recognition using computer vision
- Probability calculations and statistical analysis
- Hand strength evaluation
- Pot odds calculation
- Basic strategy suggestions
- Intuitive heads-up display (HUD) interface
- Multiple display modes for different skill levels
- Customizable settings and preferences
- Low latency performance for real-time assistance

## Technology Stack

Core Dependencies:
- Python 3.8+
- OpenCV for computer vision
- PyQt6 for the configuration interface
- SQLite for local data storage

Optional Dependencies:
- TensorFlow for machine learning models (optional)
- PyTorch for alternative ML backend (optional)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/gcheng713/PokerGlasses.git
```

2. Navigate to the project directory:
```bash
cd PokerGlasses
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

4. (Optional) Install machine learning packages if you want to train models locally:
```bash
# Install TensorFlow
pip install tensorflow

# Install PyTorch (for macOS)
pip install torch torchvision torchaudio

# For other operating systems, check PyTorch installation commands at:
# https://pytorch.org/get-started/locally/
```

5. Configure your smart glasses device settings in `config/user.yml`

6. Build and deploy to your smart glasses device:
```bash
python scripts/deploy.py
```

## Usage

1. Power on your smart glasses device

2. Launch the PokerGlasses application:
```bash
python -m pokerglasses.core.main
```

3. Calibrate the camera when prompted by looking at a blank playing card

4. The HUD will automatically activate when cards are detected in view

### Basic Controls

- Tap right temple: Toggle HUD display
- Double tap: Cycle through display modes
- Long press: Access settings menu
- Swipe forward/back: Adjust brightness

### Display Modes

- Basic: Shows only card recognition and pot odds
- Advanced: Includes equity calculations and basic strategy
- Pro: Full statistical analysis and detailed suggestions

**Note:** Remember to comply with local regulations regarding the use of assistance devices.

## Development Setup

1. Set up a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

3. Run tests:
```bash
pytest tests/
```

## Contributing

Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This project is for educational purposes only. The use of electronic devices or assistance tools during poker games may be restricted or prohibited in certain jurisdictions or venues. Always verify and comply with local regulations and casino policies.

