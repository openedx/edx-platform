from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'branding.admin')

from lms.djangoapps.branding.admin import *
