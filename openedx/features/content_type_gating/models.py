# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import namedtuple

from django.conf import settings
from django.db import models
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _

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

    enabled = models.NullBooleanField(default=None, verbose_name=_("Enabled"))

    @classmethod
    def attribute_tuple(cls):
        if hasattr(cls, '_attribute_tuple'):
            return cls._attribute_tuple

        cls._attribute_tuple = namedtuple(
            '{}Values'.format(cls.__name__),
            cls.STACKABLE_FIELDS
        )
        return cls._attribute_tuple

    @classmethod
    def configuration_stack(cls):
        if hasattr(cls, '_configuration_stack'):
            return cls._configuration_stack

        global_config = site_config = org_config = course_config = None

        stacked_config_bases = set(StackedConfigurationModel.__subclasses__())
        this_stacked_config_bases = set(cls.__bases__)

        the_stacked_config_base = stacked_config_bases & this_stacked_config_bases

        for subclass in {sub for base in the_stacked_config_base for sub in base.__subclasses__()}:
            if issubclass(subclass, GlobalContentTypeGatingConfig):
                if global_config is not None:
                    raise DuplicateConfigModelLevelError(global_config, subclass)
                global_config = subclass
            elif issubclass(subclass, SiteContentTypeGatingConfig):
                if site_config is not None:
                    raise DuplicateConfigModelLevelError(site_config, subclass)
                site_config = subclass
            elif issubclass(subclass, OrgContentTypeGatingConfig):
                if org_config is not None:
                    raise DuplicateConfigModelLevelError(org_config, subclass)
                org_config = subclass
            elif issubclass(subclass, CourseContentTypeGatingConfig):
                if course_config is not None:
                    raise DuplicateConfigModelLevelError(course_config, subclass)
                course_config = subclass

        cls._configuration_stack = (global_config, site_config, org_config, course_config)
        return cls._configuration_stack


    @classmethod
    def _stacked_current_config(cls, site=None, org=None, course=None):

        if org is None and course is not None:
            org = cls._org_from_course(course)

        if site is None and org is not None:
            site = cls._site_from_org(org)

        (global_config, site_config, org_config, course_config) = cls.configuration_stack()

        values = {}

        if global_config is not None:
            global_current = global_config.current()
            for field_name in cls.STACKABLE_FIELDS:
                field = global_config._meta.get_field(field_name)
                values[field_name] = field.value_from_object(global_current)

        print(values)

        if site_config is not None and site is not None:
            site_current = site_config.current(site)
            for field_name in cls.STACKABLE_FIELDS:
                field = site_config._meta.get_field(field_name)
                value = field.value_from_object(site_current)
                if value != field.get_default():
                    values[field_name] = value

        print(values)

        if org_config is not None and org is not None:
            org_current = org_config.current(org)
            for field_name in cls.STACKABLE_FIELDS:
                field = org_config._meta.get_field(field_name)
                value = field.value_from_object(org_current)
                if value != field.get_default():
                    values[field_name] = value

        print(values)

        if course_config is not None and course is not None:
            course_current = course_config.current(course)
            for field_name in cls.STACKABLE_FIELDS:
                field = course_config._meta.get_field(field_name)
                value = field.value_from_object(course_current)
                if value != field.get_default():
                    values[field_name] = value

        return cls.attribute_tuple()(**values)

    @classmethod
    def _org_from_course(cls, course_key):
        return course_key.org

    @classmethod
    def _site_from_org(cls, org):
        configuration = SiteConfiguration.get_configuration_for_org(org)
        if configuration is None:
            return Site.objects.get(id=settings.SITE_ID)
        else:
            return configuration.site_id


class ContentTypeGatingConfig(StackedConfigurationModel):
    class Meta(object):
        abstract = True

    enabled_after = models.DateTimeField()
    STACKABLE_FIELDS = ['enabled', 'enabled_after']

    @classmethod
    def is_enabled(cls, enrollment):
        current_config = CourseContentTypeGatingConfig.stacked_current(
            CourseOverview.objects.get(id=enrollment.course_id)
        )

        return current_config.enabled and current_config.enabled_after <= enrollment.created



class GlobalContentTypeGatingConfig(ContentTypeGatingConfig):
    pass


class SiteContentTypeGatingConfig(ContentTypeGatingConfig):
    KEY_FIELDS = ('site',)

    @classmethod
    def stacked_current(cls, site):
        return cls._stacked_current_config(site=site)


    site = models.ForeignKey('sites.Site', on_delete=models.CASCADE)


class OrgContentTypeGatingConfig(ContentTypeGatingConfig):
    KEY_FIELDS = ('org',)

    @classmethod
    def stacked_current(cls, org):
        return cls._stacked_current_config(org=org)

    org = models.CharField(max_length=255, db_index=True)


class CourseContentTypeGatingConfig(ContentTypeGatingConfig):
    KEY_FIELDS = ('course', )

    @classmethod
    def stacked_current(cls, course):
        return cls._stacked_current_config(course=course)

    course = models.ForeignKey(
        'course_overviews.CourseOverview',
        on_delete=models.DO_NOTHING,
    )
