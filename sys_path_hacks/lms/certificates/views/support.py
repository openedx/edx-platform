from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'certificates.views.support')

from lms.djangoapps.certificates.views.support import *
