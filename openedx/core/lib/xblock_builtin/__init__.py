"""
Helper functions shared by built-in XBlocks.

"""


from django.conf import settings


def get_css_dependencies(group):
    """
    Returns list of CSS dependencies belonging to `group` in settings.PIPELINE['STYLESHEETS'].

    Respects `PIPELINE['PIPELINE_ENABLED']` setting.
    """
    if settings.PIPELINE['PIPELINE_ENABLED']:
        return [settings.PIPELINE['STYLESHEETS'][group]['output_filename']]
    else:
        return settings.PIPELINE['STYLESHEETS'][group]['source_filenames']


def get_js_dependencies(group):
    """
    Returns list of JS dependencies belonging to `group` in settings.PIPELINE['JAVASCRIPT'].

    Respects `PIPELINE['PIPELINE_ENABLED']` setting.
    """
    if settings.PIPELINE['PIPELINE_ENABLED']:
        return [settings.PIPELINE['JAVASCRIPT'][group]['output_filename']]
    else:
        return settings.PIPELINE['JAVASCRIPT'][group]['source_filenames']
