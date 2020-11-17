from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.management', 'lms.djangoapps.discussion.management')

from lms.djangoapps.discussion.management import *
