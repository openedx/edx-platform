from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.apps', 'lms.djangoapps.discussion.apps')

from lms.djangoapps.discussion.apps import *
