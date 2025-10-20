#!/bin/bash
# Wrapper script to run Python scripts with cuDNN library path set
# Usage: ./scripts/run_with_cudnn.sh python scripts/try_transcription.py [args...]

# Find the virtualenv directory
VENV_DIR=$(pipenv --venv 2>/dev/null)

if [ -z "$VENV_DIR" ]; then
    echo "❌ Error: Could not find pipenv virtualenv"
    echo "   Make sure you're in the project directory and pipenv is installed"
    exit 1
fi

# Set LD_LIBRARY_PATH to include cuDNN libraries
CUDNN_LIB_PATH="$VENV_DIR/lib/python3.12/site-packages/nvidia/cudnn/lib"

if [ ! -d "$CUDNN_LIB_PATH" ]; then
    echo "⚠️  Warning: cuDNN library path not found at: $CUDNN_LIB_PATH"
    echo "   Attempting to run anyway..."
fi

export LD_LIBRARY_PATH="$CUDNN_LIB_PATH:$LD_LIBRARY_PATH"

echo "🔧 Set LD_LIBRARY_PATH to include cuDNN libraries"
echo "📁 cuDNN path: $CUDNN_LIB_PATH"
echo ""

# Run the command with pipenv
exec pipenv run "$@"
