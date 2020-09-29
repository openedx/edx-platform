from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'certificates.views')

from lms.djangoapps.certificates.views import *
