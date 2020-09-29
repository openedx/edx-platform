from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'certificates.queue')

from lms.djangoapps.certificates.queue import *
