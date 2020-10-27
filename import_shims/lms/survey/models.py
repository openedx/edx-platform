from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'survey.models')

from lms.djangoapps.survey.models import *
