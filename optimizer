#!/usr/bin/env bash
# Optimize all JPG and PNG images in eos_wallpapers folders

set -euo pipefail

# JPG optimieren
find ./eos_wallpapers* -type f \( -iname "*.jpg" -o -iname "*.jpeg" \) -print0 \
    | xargs -0 -P 6 jpegoptim --strip-all --all-progressive --max=90

# PNG optimieren
oxipng -Z -r -s -o max --fast --threads 6 ./eos_wallpapers*
