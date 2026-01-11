#!/bin/bash
# Run tesseract_qt_py viewer
# Usage: ./run_app.sh [urdf_path] [srdf_path]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate conda environment
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate tesseract_nb

# NO X11 on macOS
unset DISPLAY

# Use installed tesseract_support from conda env
# The app uses tesseract_robotics.get_tesseract_support_path() automatically

cd "$SCRIPT_DIR"
python app.py "$@"
