from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.api_urls', 'lms.djangoapps.teams.api_urls')

from lms.djangoapps.teams.api_urls import *
