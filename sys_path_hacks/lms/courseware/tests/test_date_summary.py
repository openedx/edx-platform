from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.tests.test_date_summary')

from lms.djangoapps.courseware.tests.test_date_summary import *
