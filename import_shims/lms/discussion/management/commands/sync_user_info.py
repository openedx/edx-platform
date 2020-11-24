from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.management.commands.sync_user_info', 'lms.djangoapps.discussion.management.commands.sync_user_info')

from lms.djangoapps.discussion.management.commands.sync_user_info import *
