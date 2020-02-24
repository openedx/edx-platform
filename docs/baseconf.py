"""
Base configuration file for all edx-platform documentation projects.
Use as follows:

    import sys
    from path import Path
    root = Path("../..").abspath()
    sys.path.insert(0, root)
    # pylint: disable=wrong-import-position,redefined-builtin,wildcard-import
    from ..base_conf import *

    project = "my custom project name"
    extensions = [...]
    ...
"""
import os

import edx_theme

copyright = edx_theme.COPYRIGHT  # pylint: disable=redefined-builtin
author = edx_theme.AUTHOR
version = ""
release = ""

source_suffix = [".rst"]
templates_path = ["_templates"]
master_doc = "index"
language = None
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
pygments_style = None

html_theme = "edx_theme"
html_theme_path = [edx_theme.get_html_theme_path()]
html_theme_options = {"navigation_depth": 3}
html_favicon = os.path.join(
    edx_theme.get_html_theme_path(), "edx_theme", "static", "css", "favicon.ico"
)
html_static_path = ["_static"]

intersphinx_mapping = {
    'https://docs.python.org/2.7': None,
    'django': ('https://docs.djangoproject.com/en/1.11/', 'https://docs.djangoproject.com/en/1.11/_objects/'),
}
