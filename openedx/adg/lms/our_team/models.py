"""
All models for our team app
"""
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .constants import ALLOWED_PROFILE_IMAGE_EXTENSIONS
from .helpers import validate_profile_image_size


class OurTeamMember(models.Model):
    """
    Model for team members and board of trustees in about page
    """

    name = models.CharField(verbose_name=_('Name'), max_length=150, )
    designation = models.CharField(verbose_name=_('Designation'), max_length=150, )
    image = models.ImageField(
        upload_to='team-members/images/', verbose_name=_('Image'),
        validators=[FileExtensionValidator(ALLOWED_PROFILE_IMAGE_EXTENSIONS), validate_profile_image_size],
    )
    description = models.TextField(verbose_name=_('Description'), )
    url = models.URLField(default='', verbose_name=_('URL'), blank=True, )

    class Meta:
        app_label = 'our_team'

    def __str__(self):
        return self.name
