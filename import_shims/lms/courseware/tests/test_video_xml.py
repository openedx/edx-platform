from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.test_video_xml', 'lms.djangoapps.courseware.tests.test_video_xml')

from lms.djangoapps.courseware.tests.test_video_xml import *
