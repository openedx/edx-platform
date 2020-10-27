from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.management.commands.reload_forum_users', 'lms.djangoapps.discussion.management.commands.reload_forum_users')

from lms.djangoapps.discussion.management.commands.reload_forum_users import *
