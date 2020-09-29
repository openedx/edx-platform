from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'mailing.management.commands.mailchimp_sync_announcements')

from lms.djangoapps.mailing.management.commands.mailchimp_sync_announcements import *
