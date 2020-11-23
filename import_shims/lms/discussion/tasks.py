from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.tasks', 'lms.djangoapps.discussion.tasks')

from lms.djangoapps.discussion.tasks import *
