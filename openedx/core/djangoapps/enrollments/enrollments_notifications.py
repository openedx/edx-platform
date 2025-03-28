"""
Enrollment notifications sender util.
"""
from django.conf import settings

from openedx_events.learning.data import UserNotificationData
from openedx_events.learning.signals import USER_NOTIFICATION_REQUESTED


class EnrollmentNotificationSender:
    """
    Class to send notifications to user about their enrollments.
    """

    def __init__(self, course, user_id, audit_access_expiry):
        self.course = course
        self.user_id = user_id
        self.audit_access_expiry = audit_access_expiry

    def send_audit_access_expiring_soon_notification(self):
        """
        Send audit access expiring soon notification to user
        """

        notification_data = UserNotificationData(
            user_ids=[int(self.user_id)],
            context={
                'course': self.course.name,
                'audit_access_expiry': self.audit_access_expiry,
            },
            notification_type='audit_access_expiring_soon',
            content_url=f"{settings.LEARNING_MICROFRONTEND_URL}/course/{str(self.course.id)}/home",
            app_name="enrollments",
            course_key=self.course.id,
        )
        USER_NOTIFICATION_REQUESTED.send_event(notification_data=notification_data)
