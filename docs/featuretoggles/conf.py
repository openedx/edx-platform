"""
Configuration file for the generation of feature toggle documentation.
"""
import os
import sys

import edx_theme

# -- Project information -----------------------------------------------------

project = "Open edX feature toggles"
copyright = edx_theme.COPYRIGHT  # pylint: disable=redefined-builtin
author = edx_theme.AUTHOR
release = ""

# -- General configuration ---------------------------------------------------

sys.path.append(os.path.abspath('extensions'))
extensions = ["featuretoggles"]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "edx_theme"
html_theme_path = [edx_theme.get_html_theme_path()]
html_static_path = ["_static"]
