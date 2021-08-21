from django.contrib.auth.models import User
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
    enable_all_edly_sub_org_login = models.BooleanField(default=False)

    def __str__(self):
        return '{name}: ({slug})'.format(name=self.name, slug=self.slug)


class EdlySubOrganization(TimeStampedModel):
    """
    EdlySubOrganization model for Edly.
    """
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=50, unique=True, validators=[EDLY_SLUG_VALIDATOR])

    edly_organization = models.ForeignKey(EdlyOrganization, on_delete=models.CASCADE)
    edx_organization = models.OneToOneField(Organization, on_delete=models.CASCADE, null=True, blank=True)
    edx_organizations = models.ManyToManyField(Organization, related_name='edx_organizations')
    lms_site = models.OneToOneField(Site, related_name='edly_sub_org_for_lms', on_delete=models.CASCADE)
    studio_site = models.OneToOneField(Site, related_name='edly_sub_org_for_studio', on_delete=models.CASCADE)
    preview_site = models.OneToOneField(
        Site,
        related_name='edly_sub_org_for_preview_site',
        null=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return '{name}: ({slug})'.format(name=self.name, slug=self.slug)

    @property
    def get_edx_organizations(self):
        """
        Helper method to get list of short names of edX organizations of an edly suborganization.

        Returns:
            list: List of edx organizations short names
        """
        return list(self.edx_organizations.values_list('short_name', flat=True))


class EdlyUserProfile(models.Model):
    """
    User profile model for Edly users.
    """
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='edly_profile', on_delete=models.CASCADE)
    edly_sub_organizations = models.ManyToManyField(EdlySubOrganization)
    course_activity_date = models.DateTimeField(blank=True, null=True)

    @property
    def get_linked_edly_sub_organizations(self):
        """
        Helper method to get list of slugs of edly sub organizations of a user.

        Returns:
            list: List of edly sub organizations slugs
        """
        edly_sub_org_slugs = self.edly_sub_organizations.values_list('slug', flat=True)
        return edly_sub_org_slugs
