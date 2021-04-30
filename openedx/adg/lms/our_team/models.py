"""
All models for our team app
"""
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import ALLOWED_PROFILE_IMAGE_EXTENSIONS, MAX_DESCRIPTION_LENGTH, MAX_DESIGNATION_LENGTH, MAX_NAME_LENGTH
from .helpers import validate_profile_image_size


class OurTeamManager(models.Manager):
    """
    Manager for OurTeamMember model
    """

    def team_members(self):
        """
        Returns all the `Team Member` type of OurTeamMember objects
        """
        return super().get_queryset().filter(member_type=OurTeamMember.TEAM_MEMBER)

    def board_of_trustees(self):
        """
        Returns all the `Board of Trustee` type of OurTeamMember objects
        """
        return super().get_queryset().filter(member_type=OurTeamMember.BOARD_MEMBER)


#  pylint: disable=no-member
class OurTeamMember(models.Model):
    """
    Model for team members and board of trustees in about page
    """

    name = models.CharField(
        verbose_name=_('Name'),
        max_length=MAX_NAME_LENGTH,
        help_text=_('Add a name of max {char_limit} characters').format(char_limit=MAX_NAME_LENGTH),
    )
    designation = models.CharField(
        verbose_name=_('Designation'),
        max_length=MAX_DESIGNATION_LENGTH,
        help_text=_('Add a designation of max {char_limit} characters').format(char_limit=MAX_DESIGNATION_LENGTH),
    )
    image = models.ImageField(
        upload_to='team-members/images/', verbose_name=_('Image'),
        validators=[FileExtensionValidator(ALLOWED_PROFILE_IMAGE_EXTENSIONS), validate_profile_image_size],
        help_text=_('Add a square image i.e image with 1:1 aspect ratio for optimal results')
    )
    description = models.TextField(
        verbose_name=_('Description'),
        max_length=MAX_DESCRIPTION_LENGTH,
        help_text=_('Add a description of max {char_limit} characters').format(char_limit=MAX_DESCRIPTION_LENGTH),
    )
    url = models.URLField(default='', verbose_name=_('URL'), blank=True, )

    TEAM_MEMBER = 'team_member'
    BOARD_MEMBER = 'board_of_trustee'

    TYPE_CHOICES = (
        (TEAM_MEMBER, _('Team Member')),
        (BOARD_MEMBER, _('Board Of Trustee')),
    )

    member_type = models.CharField(
        verbose_name=_('Member Type'), choices=TYPE_CHOICES, default=TEAM_MEMBER, max_length=20
    )

    objects = OurTeamManager()

    class Meta:
        app_label = 'our_team'

    def __str__(self):
        return self.name
