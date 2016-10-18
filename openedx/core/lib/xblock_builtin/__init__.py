"""
Helper functions shared by built-in XBlocks.

"""


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
