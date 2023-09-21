"""
Utilities for adding edx-platform assets to built-in XBlocks.

These should not be used to support any XBlocks outside of edx-platform.
"""
from pathlib import Path

import webpack_loader
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from openedx.core.djangoapps.theming.helpers_static import get_static_file_url


def add_sass_to_fragment(fragment, sass_relative_path):
    """
    Given a Sass path relative to xmodule/assets, add a compiled CSS URL to the fragment.

    Raises:
    * ValueError if {sass_relative_path} is absolute or does not end in '.scss'.
    * FileNotFoundError if edx-platform/xmodule/assets/{sass_relative_path} is missing.
    * ImproperlyConfigured if the lookup of the static CSS URL fails. This could happen
      if Sass wasn't compiled, CSS wasn't collected, or the staticfiles app is misconfigured.

    Notes:
    * This function is theme-aware. That is: If a theme is enabled which provides a compiled
      CSS file of the same name, then that CSS file will be used instead.
    """
    if not isinstance(sass_relative_path, Path):
        sass_relative_path = Path(sass_relative_path)
    if sass_relative_path.is_absolute():
        raise ValueError(f"sass_relative_path should be relative; is absolute: {sass_relative_path}")
    if sass_relative_path.suffix != '.scss':
        raise ValueError(f"sass_relative_path should be .scss file; is: {sass_relative_path}")
    sass_absolute_path = Path(settings.REPO_ROOT) / "xmodule" / "assets" / sass_relative_path
    if not sass_absolute_path.is_file():
        raise FileNotFoundError(f"Sass not found: {sass_absolute_path}")
    css_static_path = Path('css') / sass_relative_path.with_suffix('.css')
    css_url = get_static_file_url(str(css_static_path))  # get_static_file_url is theme-aware.
    if not css_url:
        raise ImproperlyConfigured(
            f"Did not find CSS file {css_static_path} (compiled from {sass_absolute_path}) "
            f"in staticfiles storage. Perhaps it wasn't collected?"
        )
    fragment.add_css_url(css_url)


def add_webpack_js_to_fragment(fragment, bundle_name):
    """
    Add all JS webpack chunks to the supplied fragment.
    """
    for chunk in webpack_loader.utils.get_files(bundle_name, None, 'DEFAULT'):
        if chunk['name'].endswith(('.js', '.js.gz')):
            fragment.add_javascript_url(chunk['url'])
