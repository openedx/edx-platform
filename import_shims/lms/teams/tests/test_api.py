from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.tests.test_api', 'lms.djangoapps.teams.tests.test_api')

from lms.djangoapps.teams.tests.test_api import *
