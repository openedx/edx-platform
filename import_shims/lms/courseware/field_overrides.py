from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.field_overrides')

from lms.djangoapps.courseware.field_overrides import *
