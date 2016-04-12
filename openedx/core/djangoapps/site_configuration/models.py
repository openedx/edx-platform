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


class SiteConfiguration(models.Model):
    """
    Model for storing site configuration. These configuration override OpenEdx configurations and settings.
    e.g. You can override site name, logo image, favicon etc. using site configuration.

    Fields:
        site (OneToOneField): one to one field relating each configuration to a single site
        values (JSONField):  json field to store configurations for a site
    """
    site = models.OneToOneField(Site, related_name='configuration')
    values = JSONField(
        null=False,
        blank=True,
        load_kwargs={'object_pairs_hook': collections.OrderedDict}
    )

    def __unicode__(self):
        return u"<SiteConfiguration: {site} >".format(site=self.site)

    def __repr__(self):
        return self.__unicode__()


class SiteConfigurationHistory(TimeStampedModel):
    """
    This is an archive table for SiteConfiguration, so that we can maintain a history of
    changes. Note that the site field is not unique in this model, compared to SiteConfiguration.

    Fields:
        site (ForeignKey): foreign-key to django Site
        values (JSONField): json field to store configurations for a site
    """
    site = models.ForeignKey(Site, related_name='configuration_histories')
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
    )
