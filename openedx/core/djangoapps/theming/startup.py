"""
Startup code for Comprehensive Theming
"""

from path import Path as path
from django.conf import settings

from .core import enable_comprehensive_theme


def run():
    """Enable comprehensive theming, if we should."""
    if settings.COMPREHENSIVE_THEME_DIR:
        enable_comprehensive_theme(theme_dir=path(settings.COMPREHENSIVE_THEME_DIR))
