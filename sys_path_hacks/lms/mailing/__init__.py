from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'mailing')

from lms.djangoapps.mailing import *
