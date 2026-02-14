#!/bin/bash

# Lightweight VJ Pro - Auto Setup Script for macOS
# This script installs all dependencies and prepares the environment.

echo "🚀 Starting VJ Pro Setup..."

# 1. Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "🍺 Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✅ Homebrew is already installed."
fi

# 2. Install PortAudio (required for PyAudio)
echo "🔊 Installing PortAudio via Homebrew..."
brew install portaudio

# 3. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "🐍 Python 3 not found. Installing via Homebrew..."
    brew install python
else
    echo "✅ Python 3 is already installed."
fi

# 4. Create Virtual Environment
echo "📦 Setting up Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate

# 5. Install Python Dependencies
# We need to tell pip where to find the portaudio headers on macOS
echo "🛠 Installing Python packages..."
export C_INCLUDE_PATH=$(brew --prefix portaudio)/include
export LIBRARY_PATH=$(brew --prefix portaudio)/lib

pip install --upgrade pip
pip install pyserial numpy flask mido python-rtmidi
pip install --global-option='build_ext' --global-option="-I$(brew --prefix portaudio)/include" --global-option="-L$(brew --prefix portaudio)/lib" pyaudio

echo ""
echo "✅ SETUP COMPLETE!"
echo "------------------------------------------------"
echo "To start the VJ System, run:"
echo "source venv/bin/activate && python3 main.py"
echo "------------------------------------------------"
