#!/usr/bin/env bash

# Optimize all JPG files in eos_wallpapers_classic and eos_wallpapers_community using jpegoptim
find eos_wallpapers_classic/ eos_wallpapers_community/ -iname "*.jpg" -exec jpegoptim --strip-all --all-progressive {} \;

# Optimize all PNG files in eos_wallpapers_classic and eos_wallpapers_community using zopflipng
#find eos_wallpapers_classic/ eos_wallpapers_community/ -iname '*.png' -exec zopflipng --iterations=100 --splitting=3 {} {} \;
# very very sloooow ;)

# Optimize all PNG files in eos_wallpapers_classic and eos_wallpapers_community using oxipng
find eos_wallpapers_classic/ eos_wallpapers_community/ -iname "*.png" -print0 | xargs -0 -n1 oxipng -o max --strip all --threads 2

