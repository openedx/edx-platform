from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'mobile_api.urls')

from lms.djangoapps.mobile_api.urls import *
