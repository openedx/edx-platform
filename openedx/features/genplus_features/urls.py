"""
URLs for genplus features.
"""
from django.conf.urls import url, include


genplus_url_patterns = [
    url(r'^genplus/', include('openedx.features.genplus_features.genplus.urls')),
    url(r'^genplus/learning/', include('openedx.features.genplus_features.genplus_learning.urls')),
    url(r'^genplus/teach/', include('openedx.features.genplus_features.genplus_teach.urls')),
]
