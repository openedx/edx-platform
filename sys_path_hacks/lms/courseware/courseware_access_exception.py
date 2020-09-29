from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.courseware_access_exception')

from lms.djangoapps.courseware.courseware_access_exception import *
