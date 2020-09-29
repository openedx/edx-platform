from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'survey.views')

from lms.djangoapps.survey.views import *
