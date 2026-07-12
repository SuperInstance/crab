#!/usr/bin/env python3
"""
crab — agent shell for entering and leaving repos (shells).

Like entering a MUD room: step into a repo, use its tools, step out.
"""

from .crab import CrabShell, main

__all__ = [
    "CrabShell",
    "main",
]

__version__ = "0.1.0"
