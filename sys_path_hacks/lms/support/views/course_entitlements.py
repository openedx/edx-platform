from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'support.views.course_entitlements')

from lms.djangoapps.support.views.course_entitlements import *
