#!/bin/bash
# Run tesseract_qt_py viewer
# Usage: ./run_app.sh [urdf_path] [srdf_path]

set -e
cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pixi run app -- "$@"
