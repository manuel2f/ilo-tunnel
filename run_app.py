#!/usr/bin/env python3
"""
Entry point for PyInstaller builds.
This script avoids relative import issues by calling main() directly.
"""
import sys
import os

# Ensure the package directory is in the path
if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle
    base_path = sys._MEIPASS
    sys.path.insert(0, base_path)

from ilo_tunnel.main import main

if __name__ == '__main__':
    main()
