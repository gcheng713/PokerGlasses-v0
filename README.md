# PokerGlasses

A smart glasses application designed to assist poker players by providing real-time information and analysis during gameplay.

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

- Python 3.8+
- OpenCV for computer vision
- TensorFlow for machine learning models
- PyQt6 for the configuration interface
- Custom AR display drivers
- SQLite for local data storage

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

4. Install machine learning packages if you want to train models locally:
```bash
# Install TensorFlow
pip install tensorflow

# Install PyTorch (for macOS)
pip install torch torchvision torchaudio

# For other operating systems, check PyTorch installation commands at:
# https://pytorch.org/get-started/locally/
```

5. Configure your smart glasses device settings in `config.yml`

6. Build and deploy to your smart glasses device:
```bash
python setup.py deploy
```

## Usage

1. Power on your smart glasses device

2. Launch the PokerGlasses application:
```bash
poker-glasses start
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
pip install -r requirements.txt
```

3. Run tests:
```bash
pytest tests/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This project is for educational purposes only. The use of electronic devices or assistance tools during poker games may be restricted or prohibited in certain jurisdictions or venues. Always verify and comply with local regulations and casino policies.

