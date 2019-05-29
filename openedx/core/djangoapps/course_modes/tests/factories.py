"""
Factories for course mode models.
"""
from __future__ import absolute_import

import random

from factory import lazy_attribute
from factory.django import DjangoModelFactory
from opaque_keys.edx.locator import CourseLocator

from openedx.core.djangoapps.course_modes.models import CourseMode


# Factories are self documenting
# pylint: disable=missing-docstring
class CourseModeFactory(DjangoModelFactory):
    class Meta(object):
        model = CourseMode

    course_id = CourseLocator('MITx', '999', 'Robot_Super_Course')
    mode_slug = CourseMode.DEFAULT_MODE_SLUG
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
