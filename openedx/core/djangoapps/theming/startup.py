"""
Startup code for Comprehensive Theming
"""

from .core import try_enable_theme


def run():
    """Enable comprehensive theming, if we should."""
    try_enable_theme()
