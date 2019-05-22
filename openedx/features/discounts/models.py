"""
DiscountRestrictionConfig Models
"""

# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.utils.encoding import python_2_unicode_compatible

from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel


@python_2_unicode_compatible
class DiscountRestrictionConfig(StackedConfigurationModel):
    """
    A ConfigurationModel used to manage restrictons for lms-controlled discounts
    """

    STACKABLE_FIELDS = ('enabled',)

    @classmethod
    def enabled_for_course(cls, course):
        """
        Return whether lms-controlled discounts can be enabled for this course.

        Arguments:
            course: The CourseOverview of the course being queried.
        """
        current_config = cls.current(course_key=course.id)
        return current_config.enabled

    def __str__(self):
        return "DiscountRestrictionConfig(enabled={!r})".format(
            self.enabled
        )
