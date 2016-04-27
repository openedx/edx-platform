"""
Models for the custom course feature
"""
from datetime import datetime
import logging

from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import UTC

from lazy import lazy
from xmodule_django.models import CourseKeyField, LocationKeyField  # pylint: disable=import-error
from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore.django import modulestore


log = logging.getLogger("edx.ccx")


class CustomCourseForEdX(models.Model):
    """
    A Custom Course.
    """
    course_id = CourseKeyField(max_length=255, db_index=True)
    display_name = models.CharField(max_length=255)
    coach = models.ForeignKey(User, db_index=True)

    @lazy
    def course(self):
        """Return the CourseDescriptor of the course related to this CCX"""
        store = modulestore()
        with store.bulk_operations(self.course_id):
            course = store.get_course(self.course_id)
            if not course or isinstance(course, ErrorDescriptor):
                log.error("CCX {0} from {2} course {1}".format(  # pylint: disable=logging-format-interpolation
                    self.display_name, self.course_id, "broken" if course else "non-existent"
                ))
            return course

    @lazy
    def start(self):
        """Get the value of the override of the 'start' datetime for this CCX
        """
        # avoid circular import problems
        from .overrides import get_override_for_ccx
        return get_override_for_ccx(self, self.course, 'start')

    @lazy
    def due(self):
        """Get the value of the override of the 'due' datetime for this CCX
        """
        # avoid circular import problems
        from .overrides import get_override_for_ccx
        return get_override_for_ccx(self, self.course, 'due')

    def has_started(self):
        """Return True if the CCX start date is in the past"""
        return datetime.now(UTC()) > self.start

    def has_ended(self):
        """Return True if the CCX due date is set and is in the past"""
        if self.due is None:
            return False

        return datetime.now(UTC()) > self.due

    def start_datetime_text(self, format_string="SHORT_DATE"):
        """Returns the desired text representation of the CCX start datetime

        The returned value is always expressed in UTC
        """
        i18n = self.course.runtime.service(self.course, "i18n")
        strftime = i18n.strftime
        value = strftime(self.start, format_string)
        if format_string == 'DATE_TIME':
            value += u' UTC'
        return value

    def end_datetime_text(self, format_string="SHORT_DATE"):
        """Returns the desired text representation of the CCX due datetime

        If the due date for the CCX is not set, the value returned is the empty
        string.

        The returned value is always expressed in UTC
        """
        if self.due is None:
            return ''

        i18n = self.course.runtime.service(self.course, "i18n")
        strftime = i18n.strftime
        value = strftime(self.due, format_string)
        if format_string == 'DATE_TIME':
            value += u' UTC'
        return value


class CcxFieldOverride(models.Model):
    """
    Field overrides for custom courses.
    """
    ccx = models.ForeignKey(CustomCourseForEdX, db_index=True)
    location = LocationKeyField(max_length=255, db_index=True)
    field = models.CharField(max_length=255)

    class Meta(object):
        unique_together = (('ccx', 'location', 'field'),)

    value = models.TextField(default='null')
