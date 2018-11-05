"""
Useful ConfigurationModel subclasses

StackedConfigurationModel: A ConfigurationModel that can be overridden at site, org and course levels
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import namedtuple

from django.conf import settings
from django.db import models
from django.contrib.sites.models import Site
from django.contrib.sites.requests import RequestSite
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
import crum

from config_models.models import ConfigurationModel
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class StackedConfigurationModel(ConfigurationModel):
    """
    A ConfigurationModel that stacks Global, Site, Org, and Course level
    configuration values.
    """
    class Meta(object):
        abstract = True

    KEY_FIELDS = ('site', 'org', 'course')
    STACKABLE_FIELDS = ('enabled',)

    enabled = models.NullBooleanField(default=None, verbose_name=_("Enabled"))
    site = models.ForeignKey(Site, on_delete=models.CASCADE, null=True)
    org = models.CharField(max_length=255, db_index=True, null=True)
    course = models.ForeignKey(
        CourseOverview,
        on_delete=models.DO_NOTHING,
        null=True,
    )

    @classmethod
    def attribute_tuple(cls):
        """
        Returns a namedtuple with all attributes that can be overridden on this config model.

        For example, if MyStackedConfig.STACKABLE_FIELDS = ('enabled', 'enabled_as_of', 'studio_enabled'),
        then:

            # These lines are the same
            MyStackedConfig.attribute_tuple()
            namedtuple('MyStackedConfigValues', ('enabled', 'enabled_as_of', 'studio_enabled'))

            # attribute_tuple() behavior
            MyStackedConfigValues = MyStackedConfig.attribute_tuple()
            MyStackedConfigValues(True, '10/1/18', False).enabled  # True
            MyStackedConfigValues(True, '10/1/18', False).enabled_as_of  # '10/1/18'
            MyStackedConfigValues(True, '10/1/18', False).studio_enabled  # False
        """
        if hasattr(cls, '_attribute_tuple'):
            return cls._attribute_tuple

        cls._attribute_tuple = namedtuple(
            '{}Values'.format(cls.__name__),
            cls.STACKABLE_FIELDS
        )
        return cls._attribute_tuple

    @classmethod
    def current(cls, site=None, org=None, course=None):  # pylint: disable=arguments-differ
        """
        Return the current overridden configuration at the specified level.

        Only one level may be specified at a time. Specifying multiple levels
        will result in a ValueError.

        For example, considering the following set of requirements:

            Global: Feature Disabled
            edx.org (Site): Feature Enabled
            Harvard (org): Feature Disabled
            CS50 (course): Feature Enabled

        Assuming these values had been properly configured, these calls would result

            MyStackedConfig.current()  # False
            MyStackedConfig.current(site=Site(domain='edx.org'))  # True
            MyStackedConfig.current(site=Site(domain='whitelabel.edx.org')) # False -- value derived from global setting
            MyStackedConfig.current(org='HarvardX')  # False
            MyStackedConfig.current(org='MITx')  # True -- value derived from edx.org site
            MyStackedConfig.current(course=CourseKey(org='HarvardX', course='CS50', run='2018_Q1'))  # True

            cs50 = CourseKey(org='HarvardX', course='Bio101', run='2018_Q1')
            MyStackedConfig.current(course=cs50)  # False -- value derived from HarvardX org

        The following calls would result in errors due to overspecification:

            MyStackedConfig.current(site=Site(domain='edx.org'), org='HarvardX')
            MyStackedConfig.current(site=Site(domain='edx.org'), course=cs50)
            MyStackedConfig.current(org='HarvardX', course=cs50)

        Arguments:
            site: The Site to check current values for
            org: The org to check current values for
            course: The course to check current values for

        Returns:
            An instance of :class:`cls.attribute_tuple()` with the overridden values
            specified down to the level of the supplied argument (or global values if
            no arguments are supplied).
        """
        # Raise an error if more than one of site/org/course are specified simultaneously.
        if len([arg for arg in [site, org, course] if arg is not None]) > 1:
            raise ValueError("Only one of site, org, and course can be specified")

        if org is None and course is not None:
            org = cls._org_from_course(course)

        if site is None and org is not None:
            site = cls._site_from_org(org)

        stackable_fields = [cls._meta.get_field(field_name) for field_name in cls.STACKABLE_FIELDS]
        field_defaults = {
            field.name: field.get_default()
            for field in stackable_fields
        }

        values = field_defaults.copy()

        global_current = super(StackedConfigurationModel, cls).current(None, None, None)
        for field in stackable_fields:
            values[field.name] = field.value_from_object(global_current)

        def _override_fields_with_level(level_config):
            for field in stackable_fields:
                value = field.value_from_object(level_config)
                if value != field_defaults[field.name]:
                    values[field.name] = value

        if site is not None:
            _override_fields_with_level(
                super(StackedConfigurationModel, cls).current(site, None, None)
            )

        if org is not None:
            _override_fields_with_level(
                super(StackedConfigurationModel, cls).current(None, org, None)
            )

        if course is not None:
            _override_fields_with_level(
                super(StackedConfigurationModel, cls).current(None, None, course)
            )

        return cls.attribute_tuple()(**values)

    @classmethod
    def _org_from_course(cls, course_key):
        return course_key.org

    @classmethod
    def _site_from_org(cls, org):
        configuration = SiteConfiguration.get_configuration_for_org(org)
        if configuration is None:
            try:
                return Site.objects.get(id=settings.SITE_ID)
            except Site.DoesNotExist:
                return RequestSite(crum.get_current_request())
        else:
            return configuration.site

    def clean(self):
        # fail validation if more than one of site/org/course are specified simultaneously
        if len([arg for arg in [self.site, self.org, self.course] if arg is not None]) > 1:
            raise ValidationError(
                _('Configuration may not be specified at more than one level at once.')
            )
