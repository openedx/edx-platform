"""
Add and create new modes for running courses on this particular LMS
"""
import pytz
from datetime import datetime

from django.db import models
from collections import namedtuple
from django.utils.translation import ugettext as _
from django.db.models import Q

from xmodule_django.models import CourseKeyField

Mode = namedtuple('Mode',
                  [
                      'slug',
                      'name',
                      'min_price',
                      'suggested_prices',
                      'currency',
                      'expiration_datetime',
                      'description'
                  ])


class CourseMode(models.Model):
    """
    We would like to offer a course in a variety of modes.

    """
    # the course that this mode is attached to
    course_id = CourseKeyField(max_length=255, db_index=True)

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

    # turn this mode off after the given expiration date
    expiration_date = models.DateField(default=None, null=True, blank=True)

    expiration_datetime = models.DateTimeField(default=None, null=True, blank=True)

    # optional description override
    # WARNING: will not be localized
    description = models.TextField(null=True, blank=True)

    DEFAULT_MODE = Mode('honor', _('Honor Code Certificate'), 0, '', 'usd', None, None)
    DEFAULT_MODE_SLUG = 'honor'

    class Meta:
        """ meta attributes of this model """
        unique_together = ('course_id', 'mode_slug', 'currency')

    @classmethod
    def modes_for_course(cls, course_id):
        """
        Returns a list of the non-expired modes for a given course id

        If no modes have been set in the table, returns the default mode
        """
        now = datetime.now(pytz.UTC)
        found_course_modes = cls.objects.filter(Q(course_id=course_id) &
                                                (Q(expiration_datetime__isnull=True) |
                                                Q(expiration_datetime__gte=now)))
        modes = ([Mode(
            mode.mode_slug,
            mode.mode_display_name,
            mode.min_price,
            mode.suggested_prices,
            mode.currency,
            mode.expiration_datetime,
            mode.description
        ) for mode in found_course_modes])
        if not modes:
            modes = [cls.DEFAULT_MODE]
        return modes

    @classmethod
    def modes_for_course_dict(cls, course_id):
        """
        Returns the non-expired modes for a particular course as a
        dictionary with the mode slug as the key
        """
        return {mode.slug: mode for mode in cls.modes_for_course(course_id)}

    @classmethod
    def mode_for_course(cls, course_id, mode_slug):
        """
        Returns the mode for the course corresponding to mode_slug.

        Returns only non-expired modes.

        If this particular mode is not set for the course, returns None
        """
        modes = cls.modes_for_course(course_id)

        matched = [m for m in modes if m.slug == mode_slug]
        if matched:
            return matched[0]
        else:
            return None

    @classmethod
    def verified_mode_for_course(cls, course_id):
        """
        Since we have two separate modes that can go through the verify flow,
        we want to be able to select the 'correct' verified mode for a given course.

        Currently, we prefer to return the professional mode over the verified one
        if both exist for the given course.
        """
        modes_dict = cls.modes_for_course_dict(course_id)
        verified_mode = modes_dict.get('verified', None)
        professional_mode = modes_dict.get('professional', None)
        # we prefer professional over verify
        return professional_mode if professional_mode else verified_mode

    @classmethod
    def min_course_price_for_verified_for_currency(cls, course_id, currency):
        """
        Returns the minimum price of the course int he appropriate currency over all the
        course's *verified*, non-expired modes.

        Assuming all verified courses have a minimum price of >0, this value should always
        be >0.

        If no verified mode is found, 0 is returned.
        """
        modes = cls.modes_for_course(course_id)
        for mode in modes:
            if (mode.currency == currency) and (mode.slug == 'verified'):
                return mode.min_price
        return 0

    @classmethod
    def min_course_price_for_currency(cls, course_id, currency):
        """
        Returns the minimum price of the course in the appropriate currency over all the course's
        non-expired modes.
        If there is no mode found, will return the price of DEFAULT_MODE, which is 0
        """
        modes = cls.modes_for_course(course_id)
        return min(mode.min_price for mode in modes if mode.currency == currency)

    def __unicode__(self):
        return u"{} : {}, min={}, prices={}".format(
            self.course_id.to_deprecated_string(), self.mode_slug, self.min_price, self.suggested_prices
        )


class CourseModesArchive(models.Model):
    """
    Store the past values of course_mode that a course had in the past. We decided on having
    separate model, because there is a uniqueness contraint on (course_mode, course_id)
    field pair in CourseModes. Having a separate table allows us to have an audit trail of any changes
    such as course price changes
    """
    # the course that this mode is attached to
    course_id = CourseKeyField(max_length=255, db_index=True)

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

    # turn this mode off after the given expiration date
    expiration_date = models.DateField(default=None, null=True, blank=True)

    expiration_datetime = models.DateTimeField(default=None, null=True, blank=True)
