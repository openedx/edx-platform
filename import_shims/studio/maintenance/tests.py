from import_shims.warn import warn_deprecated_import

warn_deprecated_import('maintenance.tests', 'cms.djangoapps.maintenance.tests')

from cms.djangoapps.maintenance.tests import *
