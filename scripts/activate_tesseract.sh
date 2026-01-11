#!/bin/bash
# Overlay tesseract_nb conda env onto pixi
# This bridges pixi to the pre-built tesseract environment

TESSERACT_ENV="/opt/miniconda3/envs/tesseract_nb"

if [[ ! -d "$TESSERACT_ENV" ]]; then
    echo "ERROR: tesseract_nb env not found at $TESSERACT_ENV"
    echo "Build it first: https://github.com/tesseract-robotics/tesseract_nanobind"
    return 1
fi

# Create sitecustomize.py in pixi env to add tesseract site-packages
PIXI_SITE="$CONDA_PREFIX/lib/python3.12/site-packages"
cat > "$PIXI_SITE/sitecustomize.py" << EOF
import site
site.addsitedir("$TESSERACT_ENV/lib/python3.12/site-packages")
EOF

# Shared libraries from tesseract_nb
export DYLD_LIBRARY_PATH="$TESSERACT_ENV/lib:$DYLD_LIBRARY_PATH"

# NO X11 on macOS
unset DISPLAY
