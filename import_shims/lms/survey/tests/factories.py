from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'survey.tests.factories')

from lms.djangoapps.survey.tests.factories import *
