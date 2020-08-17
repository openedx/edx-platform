"""
Configuration file for the generation of feature toggle documentation.
"""
import os

import edx_theme
import git

# -- Project information -----------------------------------------------------

project = "Open edX feature toggles"
copyright = edx_theme.COPYRIGHT  # pylint: disable=redefined-builtin
author = edx_theme.AUTHOR
release = ""

# -- General configuration ---------------------------------------------------

extensions = ["code_annotations.config_and_tools.sphinx.extensions.featuretoggles"]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

featuretoggles_source_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
featuretoggles_repo_url = "https://github.com/edx/edx-platform"
try:
    edx_platform_version = git.Repo(search_parent_directories=True).head.object.hexsha
except git.InvalidGitRepositoryError:
    edx_platform_version = "master"
featuretoggles_repo_version = edx_platform_version

# -- Options for HTML output -------------------------------------------------

html_theme = "edx_theme"
html_theme_path = [edx_theme.get_html_theme_path()]
html_static_path = ["_static"]
