from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'static_template_view.urls')

from lms.djangoapps.static_template_view.urls import *
