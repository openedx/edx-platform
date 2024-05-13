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

# .. toggle_name: notifications.show_notifications_tray
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to show notifications tray
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2023-06-07
# .. toggle_target_removal_date: 2023-12-07
# .. toggle_tickets: INF-902
SHOW_NOTIFICATIONS_TRAY = CourseWaffleFlag(f"{WAFFLE_NAMESPACE}.show_notifications_tray", __name__)

# .. toggle_name: notifications.enable_notifications_filters
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable filters in notifications task
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2023-06-07
# .. toggle_target_removal_date: 2024-06-01
# .. toggle_tickets: INF-902
ENABLE_NOTIFICATIONS_FILTERS = CourseWaffleFlag(f"{WAFFLE_NAMESPACE}.enable_notifications_filters", __name__)

# .. toggle_name: notifications.enable_coursewide_notifications
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable coursewide notifications
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2023-10-25
# .. toggle_target_removal_date: 2024-06-01
# .. toggle_tickets: INF-1145
ENABLE_COURSEWIDE_NOTIFICATIONS = CourseWaffleFlag(f"{WAFFLE_NAMESPACE}.enable_coursewide_notifications", __name__)

# .. toggle_name: notifications.enable_ora_staff_notifications
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable ORA staff notifications
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2024-04-04
# .. toggle_target_removal_date: 2024-06-04
# .. toggle_tickets: INF-1304
ENABLE_ORA_STAFF_NOTIFICATION = CourseWaffleFlag(f"{WAFFLE_NAMESPACE}.enable_ora_staff_notifications", __name__)

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
