'''
django admin pages for courseware model
'''

from student.models import UserProfile, UserTestGroup, CourseEnrollmentAllowed
from student.models import CourseEnrollment, Registration, PendingNameChange, enrollment_change
from ratelimitbackend import admin

from django.conf import settings
from django.dispatch import receiver

import analytics

admin.site.register(UserProfile)

admin.site.register(UserTestGroup)

admin.site.register(CourseEnrollment)

admin.site.register(CourseEnrollmentAllowed)

admin.site.register(Registration)

admin.site.register(PendingNameChange)

@receiver(enrollment_change, sender=CourseEnrollment)
def enrollment_change_callback(sender, **kwargs):
    """
    Callback for when an enrollment or unenrollment has been completed
    """
    if kwargs['action'] == 'enroll':
        event_message = "Enrolled in a Course"
    else:
        event_message = "Unenrolled from a Course"

    if settings.FEATURES.get('SEGMENT_IO_LMS') and settings.SEGMENT_IO_LMS_KEY:
        analytics.track(kwargs['user_id'], event_message, {
            'org': kwargs['org'],
            'course': kwargs['course'],
            'run': kwargs['run'],
            'mode': kwargs['mode']
        })
