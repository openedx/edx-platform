from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'survey.utils')

from lms.djangoapps.survey.utils import *
