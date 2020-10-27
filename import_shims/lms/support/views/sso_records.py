from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'support.views.sso_records')

from lms.djangoapps.support.views.sso_records import *
