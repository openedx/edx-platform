from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'certificates.apis.v0.views')

from lms.djangoapps.certificates.apis.v0.views import *
