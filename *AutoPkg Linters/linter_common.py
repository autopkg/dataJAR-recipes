"""
Helpers shared by the AutoPkg recipe linters.

Each linter imports these rather than carrying its own copy, whether it
runs on its own or is loaded by autopkg-linter.py.

This file must sit in the linters root, one level above each linter
folder. Run directly, a linter only has its own folder on sys.path, so
each one starts with a short shim that adds the parent folder before
importing from here. A linter copied out of the tree on its own fails
with ModuleNotFoundError.
"""

import os
import sys


def verify_environment() -> None:
    """Verify we're running in AutoPkg's Python environment.

    Calls sys.exit through the sys module at call time, because
    autopkg-linter.py swaps sys.exit while a linter runs. Don't change
    this to ``from sys import exit``.
    """
    autopkg_python = '/usr/local/autopkg/python'
    if not sys.executable.startswith('/usr/local/autopkg'):
        print("Error: This script should be run using AutoPkg's "
              "Python installation.")
        print(f"Please run this script using: {autopkg_python} "
              "<script_name.py>")
        sys.exit(1)


def clean_path(path: str) -> str:
    """Clean up path from drag and drop or manual entry."""
    path = path.strip().strip('"').strip("'")
    path = path.replace(r'\ ', ' ')
    path = path.rstrip(' ').rstrip('/')
    path = os.path.expanduser(path)
    return path
