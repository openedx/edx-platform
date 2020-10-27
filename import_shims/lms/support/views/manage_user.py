from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'support.views.manage_user')

from lms.djangoapps.support.views.manage_user import *
