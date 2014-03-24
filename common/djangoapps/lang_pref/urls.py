"""
Urls for managing language preferences
"""

from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^setlang/', 'lang_pref.views.set_language', name='lang_pref_set_language')
)
