from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'support.views.feature_based_enrollments')

from lms.djangoapps.support.views.feature_based_enrollments import *
