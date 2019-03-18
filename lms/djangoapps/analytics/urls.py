# -*- coding: utf-8 -*-

from . import views

urlpatterns = patterns(
    url(r'^global/$', views.microsite_view, name='analytics_microsite'),
)
