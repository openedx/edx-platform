"""
Configuration file for the generation of technical documentation.
"""
import os

import edx_theme
import git

# -- Project information -----------------------------------------------------

project = "edx-platform Technical Reference"
copyright = edx_theme.COPYRIGHT  # pylint: disable=redefined-builtin
author = edx_theme.AUTHOR
release = ""

# -- General configuration ---------------------------------------------------

extensions = ["code_annotations.contrib.sphinx.extensions.featuretoggles", "code_annotations.contrib.sphinx.extensions.settings"]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

edxplatform_repo_url = "https://github.com/openedx/edx-platform"
edxplatform_source_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
try:
    edx_platform_version = git.Repo(search_parent_directories=True).head.object.hexsha
except git.InvalidGitRepositoryError:
    edx_platform_version = "master"

featuretoggles_source_path = edxplatform_source_path
featuretoggles_repo_url = edxplatform_repo_url
featuretoggles_repo_version = edx_platform_version

settings_source_path = edxplatform_source_path
settings_repo_url = edxplatform_repo_url
settings_repo_version = edx_platform_version

# -- Options for HTML output -------------------------------------------------

html_theme = "edx_theme"
html_theme_path = [edx_theme.get_html_theme_path()]
html_static_path = ["_static"]
