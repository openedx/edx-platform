from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.rest_api.urls')

from cms.djangoapps.contentstore.rest_api.urls import *
