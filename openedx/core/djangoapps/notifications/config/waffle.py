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

# .. toggle_name: notifications.enable_push_notifications
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable push Notifications feature on mobile devices
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2025-05-27
# .. toggle_target_removal_date: 2026-05-27
# .. toggle_warning: When the flag is ON, Notifications will go through ace push channels.
ENABLE_PUSH_NOTIFICATIONS = CourseWaffleFlag(f'{WAFFLE_NAMESPACE}.enable_push_notifications', __name__)
