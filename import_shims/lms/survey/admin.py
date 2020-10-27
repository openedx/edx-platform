from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'survey.admin')

from lms.djangoapps.survey.admin import *
