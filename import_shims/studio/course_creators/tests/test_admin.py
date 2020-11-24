from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_creators.tests.test_admin', 'cms.djangoapps.course_creators.tests.test_admin')

from cms.djangoapps.course_creators.tests.test_admin import *
