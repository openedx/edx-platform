"""
Utils for DiscussionCourseXBlock
"""

import os

from django.conf import settings

from mako.template import Template as MakoTemplate

from path import Path as path


def _(text):
    """
    A noop underscore function that marks strings for extraction.
    """
    return text


def get_js_dependencies(group):
    """
    Returns list of JS dependencies belonging to `group` in settings.PIPELINE_JS.

    Respects `PIPELINE_ENABLED` setting.
    """
    if settings.PIPELINE_ENABLED:
        return [settings.PIPELINE_JS[group]['output_filename']]
    else:
        return settings.PIPELINE_JS[group]['source_filenames']
