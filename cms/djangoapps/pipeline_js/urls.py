"""
URL patterns for Javascript files used to load all of the XModule JS in one wad.
"""
from django.conf.urls import url

from pipeline_js.views import requirejs_xmodule, xmodule_js_files

urlpatterns = [
    url(r'^files\.json$', xmodule_js_files, name='xmodule_js_files'),
    url(r'^xmodule\.js$', requirejs_xmodule, name='requirejs_xmodule'),
]
