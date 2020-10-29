"""
DiscountRestrictionConfig Models
"""

# -*- coding: utf-8 -*-


from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel


@python_2_unicode_compatible
class DiscountRestrictionConfig(StackedConfigurationModel):
    """
    A ConfigurationModel used to manage restrictons for lms-controlled discounts
    """

    STACKABLE_FIELDS = ('disabled',)
    # Since this config disables a feature, it seemed it would be clearer to use a disabled flag instead of enabled.
    # The enabled field still exists but is not used or shown in the admin.
    disabled = models.NullBooleanField(default=None, verbose_name=_("Disabled"))

    @classmethod
    def disabled_for_course_stacked_config(cls, course):
        """
        Return whether lms-controlled discounts are disabled for this course.
        Checks if discounts are disabled for attributes of this course like Site, Partner, Course or Course Run.

        Arguments:
            course: The CourseOverview of the course being queried.
        """
        current_config = cls.current(course_key=course.id)
        return current_config.disabled

    def __str__(self):
        return "DiscountRestrictionConfig(disabled={!r})".format(
            self.disabled
        )


@python_2_unicode_compatible
class DiscountPercentageConfig(StackedConfigurationModel):
    """
    A ConfigurationModel to configure the discount percentage for the first purchase discount
    """
    STACKABLE_FIELDS = ('percentage',)
    percentage = models.PositiveIntegerField()

    def __str__(self):
        return "DiscountPercentageConfig(enabled={!r},percentage={!r})".format(
            self.enabled,
            self.percentage
        )
