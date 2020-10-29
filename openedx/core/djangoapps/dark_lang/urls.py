"""
Contains all the URLs for the Dark Language Support App
"""

from __future__ import absolute_import

from django.conf.urls import url

from openedx.core.djangoapps.dark_lang import views

app_name = 'dark_lang'
urlpatterns = [
    url(r'^$', views.PreviewLanguageFragmentView.as_view(), name='preview_lang'),
]
