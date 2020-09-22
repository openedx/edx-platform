import warnings
warnings.warn("Importing mailing.management.commands.mailchimp_sync_announcements instead of lms.djangoapps.mailing.management.commands.mailchimp_sync_announcements is deprecated", stacklevel=2)

from lms.djangoapps.mailing.management.commands.mailchimp_sync_announcements import *
