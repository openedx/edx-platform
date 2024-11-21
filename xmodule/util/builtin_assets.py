"""
Utilities for adding edx-platform assets to built-in XBlocks.

These should not be used to support any XBlocks outside of edx-platform.
"""
from pathlib import Path

import webpack_loader
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from openedx.core.djangoapps.theming.helpers_static import get_static_file_url


def add_css_to_fragment(fragment, css_relative_path):
    """
    Given a css path relative to xmodule/static/css-builtin-blocks, add the CSS URL to the fragment.

    Raises:
    * ValueError if {css_relative_path} is absolute or does not end in '.css'.
    * FileNotFoundError if edx-platform/xmodule/static/css-builtin-blocks/{css_relative_path} is missing.
    * ImproperlyConfigured if the lookup of the static CSS URL fails. This could happen
      if CSS wasn't collected, or the staticfiles app is misconfigured.
    """
    if not isinstance(css_relative_path, Path):
        css_relative_path = Path(css_relative_path)
    if css_relative_path.is_absolute():
        raise ValueError(f"css_file_name should be relative; is absolute: {css_relative_path}")
    if css_relative_path.suffix != '.css':
        raise ValueError(f"css_file_name should be .css file; is: {css_relative_path}")
    css_absolute_path = Path(settings.REPO_ROOT) / "xmodule" / "static" / "css-builtin-blocks" / css_relative_path
    if not css_absolute_path.is_file():
        raise FileNotFoundError(f"css file not found: {css_absolute_path}")
    css_static_path = Path('css-builtin-blocks') / css_relative_path.with_suffix('.css')
    css_url = get_static_file_url(str(css_static_path))
    if not css_url:
        raise ImproperlyConfigured(
            f"Did not find static CSS file {css_static_path} in staticfiles storage. Perhaps it wasn't collected?"
        )
    fragment.add_css_url(css_url)


def add_webpack_js_to_fragment(fragment, bundle_name):
    """
    Add all JS webpack chunks to the supplied fragment.
    """
    for chunk in webpack_loader.utils.get_files(bundle_name, None, 'DEFAULT'):
        if chunk['name'].endswith(('.js', '.js.gz')):
            fragment.add_javascript_url(chunk['url'])
