from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.tests.test_services', 'lms.djangoapps.teams.tests.test_services')

from lms.djangoapps.teams.tests.test_services import *
