"""
Add and create new modes for running courses on this particular LMS
"""
from django.db import models
from collections import namedtuple
from django.utils.translation import ugettext as _

Mode = namedtuple('Mode', ['slug', 'name', 'min_price', 'suggested_prices', 'currency'])


class CourseMode(models.Model):
    """
    We would like to offer a course in a variety of modes.

    """
    # the course that this mode is attached to
    course_id = models.CharField(max_length=255, db_index=True)

    # the reference to this mode that can be used by Enrollments to generate
    # similar behavior for the same slug across courses
    mode_slug = models.CharField(max_length=100)

    # The 'pretty' name that can be translated and displayed
    mode_display_name = models.CharField(max_length=255)

    # minimum price in USD that we would like to charge for this mode of the course
    min_price = models.IntegerField(default=0)

    # the suggested prices for this mode
    suggested_prices = models.CommaSeparatedIntegerField(max_length=255, blank=True, default='')

    # the currency these prices are in, using lower case ISO currency codes
    currency = models.CharField(default="usd", max_length=8)

    DEFAULT_MODE = Mode('honor', _('Honor Code Certificate'), 0, '', 'usd')
    DEFAULT_MODE_SLUG = 'honor'

    class Meta:
        """ meta attributes of this model """
        unique_together = ('course_id', 'mode_slug', 'currency')

    @classmethod
    def modes_for_course(cls, course_id):
        """
        Returns a list of the modes for a given course id

        If no modes have been set in the table, returns the default mode
        """
        found_course_modes = cls.objects.filter(course_id=course_id)
        modes = ([Mode(mode.mode_slug, mode.mode_display_name, mode.min_price, mode.suggested_prices, mode.currency)
                  for mode in found_course_modes])
        if not modes:
            modes = [cls.DEFAULT_MODE]
        return modes

    @classmethod
    def modes_for_course_dict(cls, course_id):
        return { mode.slug : mode for mode in cls.modes_for_course(course_id) }

    @classmethod
    def mode_for_course(cls, course_id, mode_slug):
        """
        Returns the mode for the course corresponding to mode_slug.

        If this particular mode is not set for the course, returns None
        """
        modes = cls.modes_for_course(course_id)

        matched = [m for m in modes if m.slug == mode_slug]
        if matched:
            return matched[0]
        else:
            return None

    def __unicode__(self):
        return u"{} : {}, min={}, prices={}".format(
            self.course_id, self.mode_slug, self.min_price, self.suggested_prices
        )
