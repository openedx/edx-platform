"""
Model to store a microsite in the database.

The object is stored as a json representation of the python dict
that would have been used in the settings.

"""
import collections
import os

from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_save, pre_delete
from django.db.models.base import ObjectDoesNotExist
from django.contrib.sites.models import Site
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import FileSystemStorage

import sass

from jsonfield.fields import JSONField
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords


class Microsite(models.Model):
    """
    This is where the information about the microsite gets stored to the db.
    To achieve the maximum flexibility, most of the fields are stored inside
    a json field.

    Notes:
        - The key field was required for the dict definition at the settings, and it
        is used in some of the microsite_configuration methods.
        - The site field is django site.
        - The values field must be validated on save to prevent the platform from crashing
        badly in the case the string is not able to be loaded as json.
    """
    site = models.OneToOneField(Site, related_name='microsite')
    key = models.CharField(max_length=63, db_index=True, unique=True)
    values = JSONField(null=False, blank=True, load_kwargs={'object_pairs_hook': collections.OrderedDict})

    def __unicode__(self):
        return self.key

    def save(self, **kwargs):
        # When creating a new object, save default microsite values. Not implemented as a default method on the field
        # because it depends on other fields that should be already filled.
        if not self.id:
            self.values = self._get_initial_microsite_values()

        # fix for a bug with some pages requiring uppercase platform_name variable
        self.values['PLATFORM_NAME'] = self.values.get('platform_name', '')

        # recompile SASS on every save
        self.compile_microsite_sass()
        #self.collect_css_file()
        return super(Microsite, self).save(**kwargs)

    def get_organizations(self):
        """
        Helper method to return a list of organizations associated with our particular Microsite
        """
        return MicrositeOrganizationMapping.get_organizations_for_microsite_by_pk(self.id)  # pylint: disable=no-member

    @classmethod
    def get_microsite_for_domain(cls, domain):
        """
        Returns the microsite associated with this domain. Note that we always convert to lowercase, or
        None if no match
        """

        # remove any port number from the hostname
        domain = domain.split(':')[0]
        microsites = cls.objects.filter(site__domain__iexact=domain)

        return microsites[0] if microsites else None


class MicrositeHistory(TimeStampedModel):
    """
    This is an archive table for Microsites model, so that we can maintain a history of changes. Note that the
    key field is no longer unique
    """
    site = models.ForeignKey(Site, related_name='microsite_history')
    key = models.CharField(max_length=63, db_index=True)
    values = JSONField(null=False, blank=True, load_kwargs={'object_pairs_hook': collections.OrderedDict})

    def __unicode__(self):
        return self.key

    class Meta(object):
        """ Meta class for this Django model """
        verbose_name_plural = "Microsite histories"


def _make_archive_copy(instance):
    """
    Helper method to make a copy of a Microsite into the history table
    """
    archive_object = MicrositeHistory(
        key=instance.key,
        site=instance.site,
        values=instance.values,
    )
    archive_object.save()


@receiver(pre_delete, sender=Microsite)
def on_microsite_deleted(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Archive the exam attempt when the item is about to be deleted
    Make a clone and populate in the History table
    """
    _make_archive_copy(instance)


@receiver(pre_save, sender=Microsite)
def on_microsite_updated(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Archive the microsite on an update operation
    """

    if instance.id:
        # on an update case, get the original and archive it
        original = Microsite.objects.get(id=instance.id)
        _make_archive_copy(original)


class MicrositeOrganizationMapping(models.Model):
    """
    Mapping of Organization to which Microsite it belongs
    """

    organization = models.CharField(max_length=63, db_index=True, unique=True)
    microsite = models.ForeignKey(Microsite, db_index=True)

    # for archiving
    history = HistoricalRecords()

    def __unicode__(self):
        """String conversion"""
        return u'{microsite_key}: {organization}'.format(
            microsite_key=self.microsite.key,
            organization=self.organization
        )

    @classmethod
    def get_organizations_for_microsite_by_pk(cls, microsite_pk):
        """
        Returns a list of organizations associated with the microsite key, returned as a set
        """
        return cls.objects.filter(microsite_id=microsite_pk).values_list('organization', flat=True)

    @classmethod
    def get_microsite_for_organization(cls, org):
        """
        Returns the microsite object for a given organization based on the table mapping, None if
        no mapping exists
        """

        try:
            item = cls.objects.select_related('microsite').get(organization=org)
            return item.microsite
        except ObjectDoesNotExist:
            return None


class MicrositeTemplate(models.Model):
    """
    A HTML template that a microsite can use
    """

    microsite = models.ForeignKey(Microsite, db_index=True)
    template_uri = models.CharField(max_length=255, db_index=True)
    template = models.TextField()

    # for archiving
    history = HistoricalRecords()

    def __unicode__(self):
        """String conversion"""
        return u'{microsite_key}: {template_uri}'.format(
            microsite_key=self.microsite.key,
            template_uri=self.template_uri
        )

    class Meta(object):
        """ Meta class for this Django model """
        unique_together = (('microsite', 'template_uri'),)

    @classmethod
    def get_template_for_microsite(cls, domain, template_uri):
        """
        Returns the template object for the microsite, None if not found
        """
        try:
            return cls.objects.get(microsite__site__domain=domain, template_uri=template_uri)
        except ObjectDoesNotExist:
            return None
