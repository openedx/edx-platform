"""
Startup code for Comprehensive Theming
"""

from path import Path as path
from django.conf import settings

from .core import enable_comprehensive_theme


def run():
    """Enable comprehensive theming, if we should."""
    if settings.COMP_THEME_DIR:
        enable_comprehensive_theme(theme_dir=path(settings.COMP_THEME_DIR))
