"""
Utilities for returning XModule JS (used by requirejs)
"""


from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage


def get_xmodule_urls():
    """
    Returns a list of the URLs to hit to grab all the XModule JS
    """
    pipeline_js_settings = settings.PIPELINE['JAVASCRIPT']["module-js"]
    if settings.DEBUG:
        paths = [path.replace(".coffee", ".js") for path in pipeline_js_settings["source_filenames"]]
    else:
        paths = [pipeline_js_settings["output_filename"]]
    return [staticfiles_storage.url(path) for path in paths]
