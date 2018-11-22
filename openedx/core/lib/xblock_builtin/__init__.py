"""
Helper functions shared by built-in XBlocks.

"""

import os

from django.conf import settings


def get_css_dependencies(group):
    """
    Returns list of CSS dependencies belonging to `group` in settings.PIPELINE_JS.

    Respects `PIPELINE_ENABLED` setting.
    """
    if settings.PIPELINE_ENABLED:
        return [settings.PIPELINE_CSS[group]['output_filename']]
    else:
        return settings.PIPELINE_CSS[group]['source_filenames']


def get_js_dependencies(group):
    """
    Returns list of JS dependencies belonging to `group` in settings.PIPELINE_JS.

    Respects `PIPELINE_ENABLED` setting.
    """
    if settings.PIPELINE_ENABLED:
        return [settings.PIPELINE_JS[group]['output_filename']]
    else:
        return settings.PIPELINE_JS[group]['source_filenames']


def package_data(pkg, root_list):
    """
    Generic function to find package_data for `pkg` under `root`.
    """
    data = []
    for root in root_list:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}
