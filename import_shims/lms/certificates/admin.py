from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'certificates.admin')

from lms.djangoapps.certificates.admin import *
