from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_api.blocks.forms')

from lms.djangoapps.course_api.blocks.forms import *
