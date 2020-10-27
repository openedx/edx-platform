from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.models')

from lms.djangoapps.courseware.models import *
