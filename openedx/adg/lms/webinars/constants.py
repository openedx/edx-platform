"""
Constants for webinars app
"""
from django.utils.translation import gettext_lazy as _

ALLOWED_BANNER_EXTENSIONS = ('png', 'jpg', 'jpeg', 'svg')
BANNER_MAX_SIZE = 2 * 1024 * 1024

STARTING_SOON_REMINDER_ID_FIELD_NAME = 'starting_soon_mandrill_reminder_id'
ONE_WEEK_REMINDER_ID_FIELD_NAME = 'week_before_mandrill_reminder_id'

WEBINAR_DATE_TIME_FORMAT = '%A, %B %d, %Y %I:%M %p AST'
WEBINAR_DATE_FORMAT = '%B %d, %Y'
WEBINAR_TIME_FORMAT = '%I:%M %p AST'
WEBINAR_DEFAULT_TIME_ZONE = 'Asia/Riyadh'

WEBINAR_STATUS_CANCELLED = _('Cancelled')
WEBINAR_STATUS_DELIVERED = _('Delivered')
WEBINAR_STATUS_UPCOMING = _('Upcoming')

WEBINARS_TIME_FORMAT = '%B %d, %Y %I:%M %p %Z'

SEND_UPDATE_EMAILS_FIELD = 'send_update_emails'
UTC_TIMEZONE_HELP_TEXT = _('Please add the time in UTC timezone.')
