from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.module_render', 'lms.djangoapps.courseware.module_render')

from lms.djangoapps.courseware.module_render import *
