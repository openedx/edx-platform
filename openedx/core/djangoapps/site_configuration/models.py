"""
Django models for site configurations.
"""
import collections

from django.db import models
from django.contrib.sites.models import Site
from django.db.models.signals import post_save
from django.dispatch import receiver

from django_extensions.db.models import TimeStampedModel
from jsonfield.fields import JSONField


from logging import getLogger
logger = getLogger(__name__)  # pylint: disable=invalid-name


class SiteConfiguration(models.Model):
    """
    Model for storing site configuration. These configuration override OpenEdx configurations and settings.
    e.g. You can override site name, logo image, favicon etc. using site configuration.

    Fields:
        site (OneToOneField): one to one field relating each configuration to a single site
        values (JSONField):  json field to store configurations for a site
    """
    site = models.OneToOneField(Site, related_name='configuration')
    enabled = models.BooleanField(default=False, verbose_name="Enabled")
    values = JSONField(
        null=False,
        blank=True,
        load_kwargs={'object_pairs_hook': collections.OrderedDict}
    )

    def __unicode__(self):
        return u"<SiteConfiguration: {site} >".format(site=self.site)

    def __repr__(self):
        return self.__unicode__()

    def get_value(self, name, default=None):
        """
        Return Configuration value for the key specified as name argument.

        Function logs a message if configuration is not enabled or if there is an error retrieving a key.

        Args:
            name (str): Name of the key for which to return configuration value.
            default: default value tp return if key is not found in the configuration

        Returns:
            Configuration value for the given key or returns `None` if configuration is not enabled.
        """
        if self.enabled:
            try:
                return self.values.get(name, default)  # pylint: disable=no-member
            except AttributeError as error:
                logger.exception('Invalid JSON data. \n [%s]', error)
        else:
            logger.info("Site Configuration is not enabled for site (%s).", self.site)

        return default

    @classmethod
    def get_value_for_org(cls, org, name, default=None):
        """
        This returns site configuration value which has an org_filter that matches
        what is passed in,

        Args:
            org (str): Course ord filter, this value will be used to filter out the correct site configuration.
            name (str): Name of the key for which to return configuration value.
            default: default value tp return if key is not found in the configuration

        Returns:
            Configuration value for the given key.
        """
        for configuration in cls.objects.filter(values__contains=org, enabled=True).all():
            org_filter = configuration.get_value('course_org_filter', None)
            if org_filter == org:
                return configuration.get_value(name, default)
        return default

    @classmethod
    def get_all_orgs(cls):
        """
        This returns all of the orgs that are considered in site configurations, This can be used,
        for example, to do filtering.

        Returns:
            Configuration value for the given key.
        """
        org_filter_set = set()
        for configuration in cls.objects.filter(values__contains='course_org_filter', enabled=True).all():
            org_filter = configuration.get_value('course_org_filter', None)
            if org_filter:
                org_filter_set.add(org_filter)
        return org_filter_set


class SiteConfigurationHistory(TimeStampedModel):
    """
    This is an archive table for SiteConfiguration, so that we can maintain a history of
    changes. Note that the site field is not unique in this model, compared to SiteConfiguration.

    Fields:
        site (ForeignKey): foreign-key to django Site
        values (JSONField): json field to store configurations for a site
    """
    site = models.ForeignKey(Site, related_name='configuration_histories')
    enabled = models.BooleanField(default=False, verbose_name="Enabled")
    values = JSONField(
        null=False,
        blank=True,
        load_kwargs={'object_pairs_hook': collections.OrderedDict}
    )

    def __unicode__(self):
        return u"<SiteConfigurationHistory: {site}, Last Modified: {modified} >".format(
            modified=self.modified,
            site=self.site,
        )

    def __repr__(self):
        return self.__unicode__()


@receiver(post_save, sender=SiteConfiguration)
def update_site_configuration_history(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Add site configuration changes to site configuration history.

    Args:
        sender: sender of the signal i.e. SiteConfiguration model
        instance: SiteConfiguration instance associated with the current signal
        **kwargs: extra key word arguments
    """
    SiteConfigurationHistory.objects.create(
        site=instance.site,
        values=instance.values,
        enabled=instance.enabled,
    )
