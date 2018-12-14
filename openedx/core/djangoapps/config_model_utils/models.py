"""
Useful ConfigurationModel subclasses

StackedConfigurationModel: A ConfigurationModel that can be overridden at site, org and course levels
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import defaultdict
from enum import Enum

from django.conf import settings
from django.db import models
from django.db.models import Q, F
from django.contrib.sites.models import Site
from django.contrib.sites.requests import RequestSite
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
import crum

from config_models.models import ConfigurationModel, cache
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class Provenance(Enum):
    """
    Provenance enum
    """
    course = 'Course'
    org = 'Org'
    site = 'Site'
    global_ = 'Global'
    default = 'Default'


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
    site = models.ForeignKey(Site, on_delete=models.CASCADE, null=True, blank=True)
    org = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    course = models.ForeignKey(
        CourseOverview,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
    )

    @classmethod
    def current(cls, site=None, org=None, course_key=None):  # pylint: disable=arguments-differ
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
        cache_key_name = cls.cache_key_name(site, org, course_key=course_key)
        cached = cache.get(cache_key_name)

        if cached is not None:
            return cached

        # Raise an error if more than one of site/org/course are specified simultaneously.
        if len([arg for arg in [site, org, course_key] if arg is not None]) > 1:
            raise ValueError("Only one of site, org, and course can be specified")

        if org is None and course_key is not None:
            org = cls._org_from_course_key(course_key)

        if site is None and org is not None:
            site = cls._site_from_org(org)

        stackable_fields = [cls._meta.get_field(field_name) for field_name in cls.STACKABLE_FIELDS]
        field_defaults = {
            field.name: field.get_default()
            for field in stackable_fields
        }

        values = field_defaults.copy()

        global_override_q = Q(site=None, org=None, course_id=None)
        site_override_q = Q(site=site, org=None, course_id=None)
        org_override_q = Q(site=None, org=org, course_id=None)
        course_override_q = Q(site=None, org=None, course_id=course_key)

        overrides = cls.objects.current_set().filter(
            global_override_q |
            site_override_q |
            org_override_q |
            course_override_q
        ).order_by(
            # Sort nulls first, and in reverse specificity order
            # so that the overrides are in the order of general to specific.
            #
            # Site | Org  | Course
            # --------------------
            # Null | Null | Null
            # site | Null | Null
            # Null | org  | Null
            # Null | Null | Course
            F('course').desc(nulls_first=True),
            F('org').desc(nulls_first=True),
            F('site').desc(nulls_first=True),
        )

        provenances = defaultdict(lambda: Provenance.default)
        for override in overrides:
            for field in stackable_fields:
                value = field.value_from_object(override)
                if value != field_defaults[field.name]:
                    values[field.name] = value
                    if override.course_id is not None:
                        provenances[field.name] = Provenance.course
                    elif override.org is not None:
                        provenances[field.name] = Provenance.org
                    elif override.site_id is not None:
                        provenances[field.name] = Provenance.site
                    else:
                        provenances[field.name] = Provenance.global_

        current = cls(**values)
        current.provenances = {field.name: provenances[field.name] for field in stackable_fields}  # pylint: disable=attribute-defined-outside-init
        cache.set(cache_key_name, current, cls.cache_timeout)
        return current

    @classmethod
    def all_current_course_configs(cls):
        """
        Return configuration for all courses
        """
        all_courses = CourseOverview.objects.all()
        all_site_configs = SiteConfiguration.objects.filter(
            values__contains='course_org_filter', enabled=True
        ).select_related('site')

        try:
            default_site = Site.objects.get(id=settings.SITE_ID)
        except Site.DoesNotExist:
            default_site = RequestSite(crum.get_current_request())

        sites_by_org = defaultdict(lambda: default_site)
        site_cfg_org_filters = (
            (site_cfg.site, site_cfg.values['course_org_filter'])
            for site_cfg in all_site_configs
        )
        sites_by_org.update({
            org: site
            for (site, orgs) in site_cfg_org_filters
            for org in (orgs if isinstance(orgs, list) else [orgs])
        })

        all_overrides = cls.objects.current_set()
        overrides = {
            (override.site_id, override.org, override.course_id): override
            for override in all_overrides
        }

        stackable_fields = [cls._meta.get_field(field_name) for field_name in cls.STACKABLE_FIELDS]
        field_defaults = {
            field.name: field.get_default()
            for field in stackable_fields
        }

        def provenance(course, field):
            """
            Return provenance for given field
            """
            for (config_key, provenance) in [
                ((None, None, course.id), Provenance.course),
                ((None, course.id.org, None), Provenance.org),
                ((sites_by_org[course.id.org].id, None, None), Provenance.site),
                ((None, None, None), Provenance.global_),
            ]:
                config = overrides.get(config_key)
                if config is None:
                    continue
                value = field.value_from_object(config)
                if value != field_defaults[field.name]:
                    return (value, provenance)

            return (field_defaults[field.name], Provenance.default)

        return {
            course.id: {
                field.name: provenance(course, field)
                for field in stackable_fields
            }
            for course in all_courses
        }

    @classmethod
    def cache_key_name(cls, site, org, course=None, course_key=None):  # pylint: disable=arguments-differ
        if course is not None and course_key is not None:
            raise ValueError("Only one of course and course_key can be specified at a time")
        if course is not None:
            course_key = course

        if site is None:
            site_id = None
        else:
            site_id = site.id

        return super(StackedConfigurationModel, cls).cache_key_name(site_id, org, course_key)

    @classmethod
    def _org_from_course_key(cls, course_key):
        return course_key.org

    @classmethod
    def _site_from_org(cls, org):
        configuration = SiteConfiguration.get_configuration_for_org(org, select_related=['site'])
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
