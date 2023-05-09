"""
Configuration file for the generation of technical documentation.
"""
import os
from datetime import datetime

import git

# -- Project information -----------------------------------------------------

project = "edx-platform Technical Reference"
copyright = f'{datetime.now().year}, Axim Collaborative, Inc'  # pylint: disable=redefined-builtin
author = 'Axim Collaborative, Inc'
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

html_theme = 'sphinx_book_theme'
html_static_path = ["_static"]
html_favicon = "https://logos.openedx.org/open-edx-favicon.ico"
html_logo = "https://logos.openedx.org/open-edx-logo-color.png"

html_theme_options = {
    "repository_url": "https://github.com/openedx/edx-platform",
    "repository_branch": "master",
    "path_to_docs": "docs/technical",
    "home_page_in_toc": True,
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
    # Please don't change unless you know what you're doing.
    "extra_footer": """
        <a rel="license" href="https://creativecommons.org/licenses/by-sa/4.0/">
            <img
                alt="Creative Commons License"
                style="border-width:0"
                src="https://i.creativecommons.org/l/by-sa/4.0/80x15.png"/>
        </a>
        <br>
        These works by
            <a
                xmlns:cc="https://creativecommons.org/ns#"
                href="https://openedx.org"
                property="cc:attributionName"
                rel="cc:attributionURL"
            >Axim Collaborative, Inc</a>
        are licensed under a
            <a
                rel="license"
                href="https://creativecommons.org/licenses/by-sa/4.0/"
            >Creative Commons Attribution-ShareAlike 4.0 International License</a>.
    """
}
