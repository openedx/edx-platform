from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'survey.exceptions')

from lms.djangoapps.survey.exceptions import *
