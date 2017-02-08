"""
Factories for course mode models.
"""
import random

from course_modes.models import CourseMode
from factory.django import DjangoModelFactory
from factory import lazy_attribute
from opaque_keys.edx.locations import SlashSeparatedCourseKey


# Factories are self documenting
# pylint: disable=missing-docstring
class CourseModeFactory(DjangoModelFactory):
    class Meta(object):
        model = CourseMode

    course_id = SlashSeparatedCourseKey('MITx', '999', 'Robot_Super_Course')
    mode_slug = 'audit'
    currency = 'usd'
    expiration_datetime = None
    suggested_prices = ''

    @lazy_attribute
    def min_price(self):
        if CourseMode.is_verified_slug(self.mode_slug):
            return random.randint(1, 100)
        return 0

    @lazy_attribute
    def mode_display_name(self):
        return '{0} course'.format(self.mode_slug)
