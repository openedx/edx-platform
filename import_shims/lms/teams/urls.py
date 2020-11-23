from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.urls', 'lms.djangoapps.teams.urls')

from lms.djangoapps.teams.urls import *
