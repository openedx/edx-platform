from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.tests', 'lms.djangoapps.discussion.tests')

from lms.djangoapps.discussion.tests import *
