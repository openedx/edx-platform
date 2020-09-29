from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.tests.test_video_handlers')

from lms.djangoapps.courseware.tests.test_video_handlers import *
