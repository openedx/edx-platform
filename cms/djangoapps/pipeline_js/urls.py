"""
URL patterns for Javascript files used to load all of the XModule JS in one wad.
"""
from django.conf.urls import url
from pipeline_js.views import xmodule_js_files, requirejs_xmodule

urlpatterns = [
    url(r'^files\.json$', xmodule_js_files, name='xmodule_js_files'),
    url(r'^xmodule\.js$', requirejs_xmodule, name='requirejs_xmodule'),
]
