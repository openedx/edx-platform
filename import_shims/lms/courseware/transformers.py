from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.transformers')

from lms.djangoapps.courseware.transformers import *
