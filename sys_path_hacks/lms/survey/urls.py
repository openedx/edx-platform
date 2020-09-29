from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'survey.urls')

from lms.djangoapps.survey.urls import *
