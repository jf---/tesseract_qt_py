#!/bin/bash
# Run tesseract_qt_py viewer
# Usage: ./run_app.sh [urdf_path] [srdf_path]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
NANOBIND_DIR="/Users/jelle/Code/CADCAM/tesseract_python_nanobind"

# Activate conda - use tesseract_nb where tesseract_robotics is built
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate tesseract_nb

# Qt6 fix
export QT_HOST_PATH=$CONDA_PREFIX

# NO X11
unset DISPLAY

# Library paths - only tesseract C++ libs + this env (avoid inheriting other envs)
export DYLD_LIBRARY_PATH="$NANOBIND_DIR/ws/install/lib:$CONDA_PREFIX/lib"

# Tesseract resource paths
export TESSERACT_SUPPORT_DIR="$NANOBIND_DIR/ws/src/tesseract/tesseract_support"
export TESSERACT_RESOURCE_PATH="$NANOBIND_DIR/ws/src/tesseract/"

# Task composer config
export TESSERACT_TASK_COMPOSER_DIR="$NANOBIND_DIR/ws/src/tesseract_planning/tesseract_task_composer"
export TESSERACT_TASK_COMPOSER_CONFIG_FILE="$TESSERACT_TASK_COMPOSER_DIR/config/task_composer_plugins.yaml"

# Check if C++ libs are built
if [ ! -d "$NANOBIND_DIR/ws/install/lib" ]; then
    echo "Warning: tesseract C++ libs not found at $NANOBIND_DIR/ws/install/lib"
    echo "Run: cd $NANOBIND_DIR && ./build_tesseract_cpp.sh"
    echo ""
fi

cd "$SCRIPT_DIR"
python app.py "$@"
