from json import dumps
from datetime import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _

from pytz import UTC
from jsonfield.fields import JSONField
from model_utils import Choices
from model_utils.models import TimeStampedModel
from openedx.features.philu_utils.backend_storage import CustomS3Storage
from openedx.features.philu_utils.utils import bytes_to_mb
from util.philu_utils import UploadToPathAndRename

from .constants import PARTNER_USER_STATUS_APPROVED, PARTNER_USER_STATUS_WAITING, PARTNER_IMAGE_MAX_SIZE


class Partner(TimeStampedModel):
    """
    This model represents white-labelled partners.
    """
    performance_url = models.URLField(blank=True, default=None)
    label = models.CharField(max_length=100, help_text="Display as a title in landing page.")
    logo = models.ImageField(
        storage=CustomS3Storage(), max_length=500, help_text="Main logo in landing page.",
        upload_to=UploadToPathAndRename(path='images', name_prefix='logo', add_path_prefix=True)
    )
    slug = models.CharField(max_length=100, unique=True, help_text="A unique identifier for an organization")
    email = models.EmailField(help_text="Contact email of an organization")
    configuration = JSONField(null=False, blank=True, default=dumps({"USER_LIMIT": ""}))
    main_title = models.CharField(blank=True, max_length=100, help_text="Display on partners landing page as main title.")
    main_description = models.TextField(blank=True, help_text="Brief description of partners landing page.")
    main_bg_image = models.ImageField(
        blank=True, storage=CustomS3Storage(), max_length=500,
        validators=[FileExtensionValidator(['jpg', 'png'], )], verbose_name=_('ADD MAIN BACKGROUND IMAGE'),
        help_text=format_lazy(
            _('Accepted extensions: .jpg, .png (maximum {mb} MB)'), mb=bytes_to_mb(PARTNER_IMAGE_MAX_SIZE)
        ), upload_to=UploadToPathAndRename(path='images', name_prefix='main_bg_image', add_path_prefix=True)
    )
    parallax_bg_image = models.ImageField(
        blank=True, storage=CustomS3Storage(), max_length=500,
        validators=[FileExtensionValidator(['jpg', 'png'], )], verbose_name=_('ADD PARALLAX BACKGROUND IMAGE'),
        help_text=format_lazy(
            _('Accepted extensions: .jpg, .png (maximum {mb} MB)'), mb=bytes_to_mb(PARTNER_IMAGE_MAX_SIZE)
        ), upload_to=UploadToPathAndRename(path='images', name_prefix='main_bg_image', add_path_prefix=True)
    )
    heading1 = models.CharField(blank=True, max_length=100, help_text="Heading 1")
    heading1_description = models.TextField(blank=True)
    heading2 = models.CharField(blank=True, max_length=100, help_text="Heading 2")
    heading2_description = models.TextField(blank=True)
    testimonials1 = JSONField(blank=True, default=dumps({"description": "", "qoute_by": "", "address": ""}))
    testimonials2 = JSONField(blank=True, default=dumps({"description": "", "qoute_by": "", "address": ""}))
    partnership_year = models.PositiveIntegerField(blank=True, default=datetime.now(UTC).year)

    def __unicode__(self):
        return '{}'.format(self.label)

    class Meta:
        verbose_name = "Partner"
        verbose_name_plural = "Partners"

    def clean(self, *args, **kwargs):
        user_limit = self.configuration.get("USER_LIMIT")
        if user_limit is None or user_limit == "":
            pass
        elif not isinstance(user_limit, basestring) or not user_limit.isdigit():
            raise ValidationError({
                "configuration": ValidationError("USER_LIMIT can only be an integer string or blank string"),
            })
        super(Partner, self).clean(*args, **kwargs)


class PartnerUser(TimeStampedModel):
    """
    This model represents all the users that are associated to a partner.
    """

    USER_STATUS = Choices(PARTNER_USER_STATUS_WAITING, PARTNER_USER_STATUS_APPROVED)

    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE, related_name="partner_user")
    partner = models.ForeignKey(Partner, db_index=True, on_delete=models.CASCADE, related_name="partner")
    status = models.CharField(max_length=32, choices=USER_STATUS, default=PARTNER_USER_STATUS_APPROVED)

    def __unicode__(self):
        return '{partner}-{user}'.format(partner=self.partner.label, user=self.user.username)

    class Meta:
        unique_together = ('user', 'partner')


class PartnerCommunity(models.Model):
    community_id = models.IntegerField()
    partner = models.ForeignKey(Partner, db_index=True, on_delete=models.CASCADE, related_name='communities')

    class Meta:
        unique_together = ('community_id', 'partner')
