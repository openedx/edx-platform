"""
Models for reverification features common to both lms and studio
"""
from datetime import datetime
import pytz

from django.core.exceptions import ValidationError
from django.db import models
from util.validate_on_save import ValidateOnSaveMixin
from xmodule_django.models import CourseKeyField


class MidcourseReverificationWindow(ValidateOnSaveMixin, models.Model):
    """
    Defines the start and end times for midcourse reverification for a particular course.

    There can be many MidcourseReverificationWindows per course, but they cannot have
    overlapping time ranges.  This is enforced by this class's clean() method.
    """
    # the course that this window is attached to
    course_id = CourseKeyField(max_length=255, db_index=True)
    start_date = models.DateTimeField(default=None, null=True, blank=True)
    end_date = models.DateTimeField(default=None, null=True, blank=True)

    def clean(self):
        """
        Gives custom validation for the MidcourseReverificationWindow model.
        Prevents overlapping windows for any particular course.
        """
        query = MidcourseReverificationWindow.objects.filter(
            course_id=self.course_id,
            end_date__gte=self.start_date,
            start_date__lte=self.end_date
        )
        if query.count() > 0:
            raise ValidationError('Reverification windows cannot overlap for a given course.')

    @classmethod
    def window_open_for_course(cls, course_id):
        """
        Returns a boolean, True if the course is currently asking for reverification, else False.
        """
        now = datetime.now(pytz.UTC)
        return cls.get_window(course_id, now) is not None

    @classmethod
    def get_window(cls, course_id, date):
        """
        Returns the window that is open for a particular course for a particular date.
        If no such window is open, or if more than one window is open, returns None.
        """
        try:
            return cls.objects.get(course_id=course_id, start_date__lte=date, end_date__gte=date)
        except cls.DoesNotExist:
            return None
