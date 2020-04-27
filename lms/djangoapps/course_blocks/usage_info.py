"""
Declares CourseUsageInfo class to be used by the transform method in
Transformers.
"""


from lms.djangoapps.courseware.access import _has_access_to_course


class CourseUsageInfo(object):
    '''
    A class object that encapsulates the course and user context to be
    used as currency across block structure transformers, by passing
    an instance of it in calls to BlockStructureTransformer.transform
    methods.
    '''
    def __init__(self, course_key, user, allow_start_dates_in_future=False):
        # Course identifier (opaque_keys.edx.keys.CourseKey)
        self.course_key = course_key

        # User object (django.contrib.auth.models.User)
        self.user = user

        # Sometimes we want to allow blocks to be returned that can bypass the
        # StartDateTransformer's filter to show blocks with start dates in the future.
        # One use case of this is for the Dates page where we want to display
        # assignments that have not yet been released.
        self.allow_start_dates_in_future = allow_start_dates_in_future

        # Cached value of whether the user has staff access (bool/None)
        self._has_staff_access = None

    @property
    def has_staff_access(self):
        '''
        Returns whether the user has staff access to the course
        associated with this CourseUsageInfo instance.

        For performance reasons (minimizing multiple SQL calls), the
        value is cached within this instance.
        '''
        if self._has_staff_access is None:
            self._has_staff_access = _has_access_to_course(self.user, 'staff', self.course_key)
        return self._has_staff_access
