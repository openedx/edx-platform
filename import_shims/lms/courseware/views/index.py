from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.views.index')

from lms.djangoapps.courseware.views.index import *
