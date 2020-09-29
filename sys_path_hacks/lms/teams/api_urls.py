from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'teams.api_urls')

from lms.djangoapps.teams.api_urls import *
