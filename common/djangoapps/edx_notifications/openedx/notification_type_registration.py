"""
Notifications type receivers that register
their particular Notifications Types when they receive
the signal
"""

# we need to import these (even unused) because they need to register their
# signal receivers
import edx_notifications.openedx.course_announcements  # pylint: disable=unused-import
import edx_notifications.openedx.forums  # pylint: disable=unused-import
import edx_notifications.openedx.leaderboard  # pylint: disable=unused-import
import edx_notifications.openedx.group_project  # pylint: disable=unused-import
import edx_notifications.openedx.mobile_apps  # pylint: disable=unused-import
