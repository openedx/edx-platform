from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'mailing.management.commands.mailchimp_sync_course')

from lms.djangoapps.mailing.management.commands.mailchimp_sync_course import *
