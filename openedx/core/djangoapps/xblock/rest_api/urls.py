"""
URL configuration for the new XBlock API
"""
from django.conf.urls import include, url

from . import views

# Note that the exact same API URLs are used in Studio and the LMS, but the API
# may act a bit differently in each (e.g. Studio stores user state ephemerally).
# If necessary at some point in the future, these URLs could be duplicated into
# urls_studio and urls_lms, and/or the views could be likewise duplicated.
app_name = 'openedx.core.djangoapps.xblock.rest_api'

urlpatterns = [
    url(r'^api/xblock/v2/', include([
        url(r'^xblocks/(?P<usage_key_str>[^/]+)/', include([
            # get metadata about an XBlock:
            url(r'^$', views.block_metadata),
            # render one of this XBlock's views (e.g. student_view)
            url(r'^view/(?P<view_name>[\w\-]+)/$', views.render_block_view),
            # get the URL needed to call this XBlock's handlers
            url(r'^handler_url/(?P<handler_name>[\w\-]+)/$', views.get_handler_url),
            # call one of this block's handlers
            url(
                r'^handler/(?P<user_id>\w+)-(?P<secure_token>\w+)/(?P<handler_name>[\w\-]+)/(?P<suffix>.+)?$',
                views.xblock_handler,
                name='xblock_handler',
            ),
        ])),
    ])),
]
