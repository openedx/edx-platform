"""
This module contains various configuration settings via
waffle switches for the notifications app.
"""

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlag

WAFFLE_NAMESPACE = 'notifications'

# .. toggle_name: notifications.enable_notifications
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable the Notifications feature
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2023-05-05
# .. toggle_target_removal_date: 2023-11-05
# .. toggle_warning: When the flag is ON, Notifications feature is enabled.
# .. toggle_tickets: INF-866
ENABLE_NOTIFICATIONS = CourseWaffleFlag(f'{WAFFLE_NAMESPACE}.enable_notifications', __name__)

# .. toggle_name: notifications.enable_email_notifications
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable the Email Notifications feature
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2024-03-25
# .. toggle_target_removal_date: 2025-06-01
# .. toggle_warning: When the flag is ON, Email Notifications feature is enabled.
# .. toggle_tickets: INF-1259
ENABLE_EMAIL_NOTIFICATIONS = WaffleFlag(f'{WAFFLE_NAMESPACE}.enable_email_notifications', __name__)

# .. toggle_name: notifications.enable_ora_grade_notifications
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable ORA grade notifications
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2024-09-10
# .. toggle_target_removal_date: 2024-10-10
# .. toggle_tickets: INF-1304
ENABLE_ORA_GRADE_NOTIFICATION = CourseWaffleFlag(f"{WAFFLE_NAMESPACE}.enable_ora_grade_notifications", __name__)

# .. toggle_name: notifications.enable_notification_grouping
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable the Notifications Grouping feature
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2024-07-22
# .. toggle_target_removal_date: 2025-06-01
# .. toggle_warning: When the flag is ON, Notifications Grouping feature is enabled.
# .. toggle_tickets: INF-1472
ENABLE_NOTIFICATION_GROUPING = CourseWaffleFlag(f'{WAFFLE_NAMESPACE}.enable_notification_grouping', __name__)


# .. toggle_name: notifications.enable_account_level_preferences
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable account level preferences for notifications
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2025-04-29
# .. toggle_target_removal_date: 2025-07-29
# .. toggle_warning: When the flag is ON, account level preferences for notifications are enabled.
# .. toggle_tickets: INF-1472
ENABLE_ACCOUNT_LEVEL_PREFERENCES = WaffleFlag(f'{WAFFLE_NAMESPACE}.enable_account_level_preferences', __name__)
