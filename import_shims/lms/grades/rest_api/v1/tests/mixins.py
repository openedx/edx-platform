from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.rest_api.v1.tests.mixins')

from lms.djangoapps.grades.rest_api.v1.tests.mixins import *
