#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Provides a URL for testing
"""

from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from web_fragments.examples.views import EXAMPLE_FRAGMENT_VIEW_NAME, ExampleFragmentView

urlpatterns = [
    url(r'^test_fragment$', ExampleFragmentView.as_view(), name=EXAMPLE_FRAGMENT_VIEW_NAME),
]
