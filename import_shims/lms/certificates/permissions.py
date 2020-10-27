from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'certificates.permissions')

from lms.djangoapps.certificates.permissions import *
