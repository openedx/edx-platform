import warnings
warnings.warn("Importing mailing.management.commands.mailchimp_sync_course instead of lms.djangoapps.mailing.management.commands.mailchimp_sync_course is deprecated", stacklevel=2)

from lms.djangoapps.mailing.management.commands.mailchimp_sync_course import *
