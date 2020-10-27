from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'survey.apps')

from lms.djangoapps.survey.apps import *
