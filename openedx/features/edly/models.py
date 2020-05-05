from django.contrib.sites.models import Site
from django.core.validators import RegexValidator
from django.db import models
from model_utils.models import TimeStampedModel
from organizations.models import Organization

EDLY_SLUG_VALIDATOR = RegexValidator(r'^[0-9a-z-]*$', 'Only small case alphanumeric and hyphen characters are allowed.')


class EdlyOrganization(TimeStampedModel):
    """
    EdlyOrganization model for Edly.
    """
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=50, unique=True, validators=[EDLY_SLUG_VALIDATOR])

    def __str__(self):
        return '{name}: ({slug})'.format(name=self.name, slug=self.slug)


class EdlySubOrganization(TimeStampedModel):
    """
    EdlySubOrganization model for Edly.
    """
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=50, unique=True, validators=[EDLY_SLUG_VALIDATOR])

    edly_organization = models.ForeignKey(EdlyOrganization)
    edx_organization = models.OneToOneField(Organization)
    lms_site = models.OneToOneField(Site, related_name='lms_site')
    studio_site = models.OneToOneField(Site, related_name='studio_site')

    class Meta:
        unique_together = (('edly_organization', 'edx_organization'),)

    def __str__(self):
        return '{name}: ({slug})'.format(name=self.name, slug=self.slug)
