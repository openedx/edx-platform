from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.test_word_cloud', 'lms.djangoapps.courseware.tests.test_word_cloud')

from lms.djangoapps.courseware.tests.test_word_cloud import *
