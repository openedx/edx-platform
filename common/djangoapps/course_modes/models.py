"""
Add and create new modes for running courses on this particular LMS
"""
import pytz
from datetime import datetime

from django.db import models
from collections import namedtuple, defaultdict
from django.utils.translation import ugettext_lazy as _
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

    # Modes that allow a student to pursue a verified certificate
    VERIFIED_MODES = ["verified", "professional"]

    class Meta:
        """ meta attributes of this model """
        unique_together = ('course_id', 'mode_slug', 'currency')

    @classmethod
    def all_modes_for_courses(cls, course_id_list):
        """Find all modes for a list of course IDs, including expired modes.

        Courses that do not have a course mode will be given a default mode.

        Arguments:
            course_id_list (list): List of `CourseKey`s

        Returns:
            dict mapping `CourseKey` to lists of `Mode`

        """
        modes_by_course = defaultdict(list)
        for mode in cls.objects.filter(course_id__in=course_id_list):
            modes_by_course[mode.course_id].append(mode.to_tuple())

        # Assign default modes if nothing available in the database
        missing_courses = set(course_id_list) - set(modes_by_course.keys())
        for course_id in missing_courses:
            modes_by_course[course_id] = [cls.DEFAULT_MODE]

        return modes_by_course

    @classmethod
    def all_and_unexpired_modes_for_courses(cls, course_id_list):
        """Retrieve course modes for a list of courses.

        To reduce the number of database queries, this function
        loads *all* course modes, then creates a second list
        of unexpired course modes.

        Arguments:
            course_id_list (list of `CourseKey`): List of courses for which
                to retrieve course modes.

        Returns:
            Tuple of `(all_course_modes, unexpired_course_modes)`, where
            the first is a list of *all* `Mode`s (including expired ones),
            and the second is a list of only unexpired `Mode`s.

        """
        now = datetime.now(pytz.UTC)
        all_modes = cls.all_modes_for_courses(course_id_list)
        unexpired_modes = {
            course_id: [
                mode for mode in modes
                if mode.expiration_datetime is None or mode.expiration_datetime >= now
            ]
            for course_id, modes in all_modes.iteritems()
        }

        return (all_modes, unexpired_modes)

    @classmethod
    def paid_modes_for_course(cls, course_id):
        """
        Returns a list of non-expired modes for a course ID that have a set minimum price.

        If no modes have been set, returns an empty list.

        Args:
            course_id (CourseKey): The course to find paid modes for.

        Returns:
            A list of CourseModes with a minimum price.

        """
        now = datetime.now(pytz.UTC)
        found_course_modes = cls.objects.filter(
            Q(course_id=course_id) &
            Q(min_price__gt=0) &
            (
                Q(expiration_datetime__isnull=True) |
                Q(expiration_datetime__gte=now)
            )
        )
        return [mode.to_tuple() for mode in found_course_modes]

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
        modes = ([mode.to_tuple() for mode in found_course_modes])
        if not modes:
            modes = [cls.DEFAULT_MODE]
        return modes

    @classmethod
    def modes_for_course_dict(cls, course_id, modes=None):
        """Returns the non-expired modes for a particular course.

        Arguments:
            course_id (CourseKey): Search for course modes for this course.

        Keyword Arguments:
            modes (list of `Mode`): If provided, search through this list
                of course modes.  This can be used to avoid an additional
                database query if you have already loaded the modes list.

        Returns:
            dict: Keys are mode slugs, values are lists of `Mode` namedtuples.

        """
        if modes is None:
            modes = cls.modes_for_course(course_id)
        return {mode.slug: mode for mode in modes}

    @classmethod
    def mode_for_course(cls, course_id, mode_slug, modes=None):
        """Returns the mode for the course corresponding to mode_slug.

        Returns only non-expired modes.

        If this particular mode is not set for the course, returns None

        Arguments:
            course_id (CourseKey): Search for course modes for this course.
            mode_slug (str): Search for modes with this slug.

        Keyword Arguments:
            modes (list of `Mode`): If provided, search through this list
                of course modes.  This can be used to avoid an additional
                database query if you have already loaded the modes list.

        Returns:
            Mode

        """
        if modes is None:
            modes = cls.modes_for_course(course_id)

        matched = [m for m in modes if m.slug == mode_slug]
        if matched:
            return matched[0]
        else:
            return None

    @classmethod
    def verified_mode_for_course(cls, course_id, modes=None):
        """Find a verified mode for a particular course.

        Since we have multiple modes that can go through the verify flow,
        we want to be able to select the 'correct' verified mode for a given course.

        Currently, we prefer to return the professional mode over the verified one
        if both exist for the given course.

        Arguments:
            course_id (CourseKey): Search for course modes for this course.

        Keyword Arguments:
            modes (list of `Mode`): If provided, search through this list
                of course modes.  This can be used to avoid an additional
                database query if you have already loaded the modes list.

        Returns:
            Mode or None

        """
        modes_dict = cls.modes_for_course_dict(course_id, modes=modes)
        verified_mode = modes_dict.get('verified', None)
        professional_mode = modes_dict.get('professional', None)
        # we prefer professional over verify
        return professional_mode if professional_mode else verified_mode

    @classmethod
    def has_verified_mode(cls, course_mode_dict):
        """Check whether the modes for a course allow a student to pursue a verfied certificate.

        Args:
            course_mode_dict (dictionary mapping course mode slugs to Modes)

        Returns:
            bool: True iff the course modes contain a verified track.

        """
        for mode in cls.VERIFIED_MODES:
            if mode in course_mode_dict:
                return True
        return False

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
    def has_payment_options(cls, course_id):
        """Determines if there is any mode that has payment options

        Check the dict of course modes and see if any of them have a minimum price or
        suggested prices. Returns True if any course mode has a payment option.

        Args:
            course_mode_dict (dict): Dictionary mapping course mode slugs to Modes

        Returns:
            True if any course mode has a payment option.

        """
        for mode in cls.modes_for_course(course_id):
            if mode.min_price > 0 or mode.suggested_prices != '':
                return True
        return False

    @classmethod
    def can_auto_enroll(cls, course_id, modes_dict=None):
        """Check whether students should be auto-enrolled in the course.

        If a course is behind a paywall (e.g. professional ed or white-label),
        then users should NOT be auto-enrolled.  Instead, the user will
        be enrolled when he/she completes the payment flow.

        Otherwise, users can be enrolled in the default mode "honor"
        with the option to upgrade later.

        Args:
            course_id (CourseKey): The course to check.

        Keyword Args:
            modes_dict (dict): If provided, use these course modes.
                Useful for avoiding unnecessary database queries.

        Returns:
            bool

        """
        if modes_dict is None:
            modes_dict = cls.modes_for_course_dict(course_id)

        # Professional mode courses are always behind a paywall
        if "professional" in modes_dict:
            return False

        # White-label uses course mode honor with a price
        # to indicate that the course is behind a paywall.
        if cls.is_white_label(course_id, modes_dict=modes_dict):
            return False

        # Check that the default mode is available.
        return ("honor" in modes_dict)

    @classmethod
    def is_white_label(cls, course_id, modes_dict=None):
        """Check whether a course is a "white label" (paid) course.

        By convention, white label courses have a course mode slug "honor"
        and a price.

        Args:
            course_id (CourseKey): The course to check.

        Keyword Args:
            modes_dict (dict): If provided, use these course modes.
                Useful for avoiding unnecessary database queries.

        Returns:
            bool

        """
        if modes_dict is None:
            modes_dict = cls.modes_for_course_dict(course_id)

        # White-label uses course mode honor with a price
        # to indicate that the course is behind a paywall.
        if "honor" in modes_dict and len(modes_dict) == 1:
            if modes_dict["honor"].min_price > 0 or modes_dict["honor"].suggested_prices != '':
                return True
        return False

    @classmethod
    def min_course_price_for_currency(cls, course_id, currency):
        """
        Returns the minimum price of the course in the appropriate currency over all the course's
        non-expired modes.
        If there is no mode found, will return the price of DEFAULT_MODE, which is 0
        """
        modes = cls.modes_for_course(course_id)
        return min(mode.min_price for mode in modes if mode.currency == currency)

    def to_tuple(self):
        """
        Takes a mode model and turns it into a model named tuple.

        Returns:
            A 'Model' namedtuple with all the same attributes as the model.

        """
        return Mode(
            self.mode_slug,
            self.mode_display_name,
            self.min_price,
            self.suggested_prices,
            self.currency,
            self.expiration_datetime,
            self.description
        )

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
