#!/usr/bin/env bash
set -euo pipefail
# One-line installer for carbon-region-picker
# Usage: curl -fsSL https://raw.githubusercontent.com/fabiocicerchia/carbon-region-picker/main/install.sh | bash

if command -v pipx &>/dev/null; then
  pipx install git+https://github.com/fabiocicerchia/carbon-region-picker
else
  pip install --user git+https://github.com/fabiocicerchia/carbon-region-picker
fi
echo "carbon-region-picker installed. Run: carbon-region-picker --help"
