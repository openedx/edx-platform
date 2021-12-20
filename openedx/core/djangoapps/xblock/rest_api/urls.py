"""
URL configuration for the new XBlock API
"""
from django.urls import include, path, re_path
from . import views

# Note that the exact same API URLs are used in Studio and the LMS, but the API
# may act a bit differently in each (e.g. Studio stores user state ephemerally).
# If necessary at some point in the future, these URLs could be duplicated into
# urls_studio and urls_lms, and/or the views could be likewise duplicated.
app_name = 'openedx.core.djangoapps.xblock.rest_api'

urlpatterns = [
    path('api/xblock/v2/', include([
        path('xblocks/<str:usage_key_str>/', include([
            # get metadata about an XBlock:
            path('', views.block_metadata),
            # render one of this XBlock's views (e.g. student_view)
            re_path(r'^view/(?P<view_name>[\w\-]+)/$', views.render_block_view),
            # get the URL needed to call this XBlock's handlers
            re_path(r'^handler_url/(?P<handler_name>[\w\-]+)/$', views.get_handler_url),
            # call one of this block's handlers
            re_path(
                r'^handler/(?P<user_id>\w+)-(?P<secure_token>\w+)/(?P<handler_name>[\w\-]+)/(?P<suffix>.+)?$',
                views.xblock_handler,
                name='xblock_handler',
            ),
        ])),
    ])),
]
