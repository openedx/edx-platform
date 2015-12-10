"""
Models for the credentials service.
"""
from __future__ import unicode_literals
import uuid  # pylint: disable=unused-import

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from model_utils.models import TimeStampedModel
from openedx.core.djangoapps.credentials_service.mixin import assets_path
from xmodule_django.models import CourseKeyField


MODE_CHOICES = (
    (_('Honor'), 'honor'),
    (_('Verified'), 'verified'),
    (_('Professional'), 'professional'),
)


def validate_image(image):
    """
    Validates that a particular image is small enough.
    """
    if image.size > (250 * 1024):
        raise ValidationError(_('The image file size must be less than 250KB.'))


class AbstractCredential(TimeStampedModel):
    """
    Abstract Credentials configuration model.
    """
    site = models.ForeignKey(Site)
    is_active = models.BooleanField(default=False)

    class Meta(object):
        abstract = True


class Signatory(TimeStampedModel):
    """
    Signatory model to add certificate signatories.
    """
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    image = models.ImageField(
        help_text=_(
            'Image must be square PNG files. The file size should be under 250KB.'
        ),
        upload_to=assets_path,
        validators=[validate_image]
    )

    def __unicode__(self):
        """Unicode representation. """
        return '{name}, {title}'.format(
            name=self.name,
            title=self.title,
        )

    def save(self, *args, **kwargs):
        """save the Signatory."""
        if self.pk is None:
            temp_image = self.image
            self.image = None
            super(Signatory, self).save(*args, **kwargs)
            self.image = temp_image

        super(Signatory, self).save(*args, **kwargs)


class CertificateTemplate(TimeStampedModel):
    """
    Certificate Template model to organize content for certificates.
    """

    name = models.CharField(max_length=255, db_index=True)
    content = models.TextField(
        help_text=_('HTML Template content data.')
    )
    certificate_type = models.CharField(
        max_length=255, null=True, blank=True,
        choices=MODE_CHOICES,
    )
    organization_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Organization with which this template is attached.'),
    )

    def __unicode__(self):
        """Unicode representation. """
        return '{name}'.format(
            name=self.name
        )


class AbstractCertificate(AbstractCredential):
    """
    Abstract Certificate configuration to support multiple type of certificates
    i.e. Programs, Courses.
    """
    signatories = models.ManyToManyField(Signatory)
    template = models.ManyToManyField(CertificateTemplate, null=True, blank=True)
    title = models.CharField(
        max_length=255, null=True, blank=True,
        help_text='Custom certificate title to override default display_name for a course/program.'
    )

    class Meta(object):
        abstract = True


class CourseCertificate(AbstractCertificate):
    """
    Configuration for Course Certificates.
    """
    course_id = CourseKeyField(max_length=255)
    certificate_type = models.CharField(
        max_length=255,
        choices=MODE_CHOICES
    )

    class Meta(object):
        unique_together = (('course_id', 'certificate_type', 'site'),)

    def __unicode__(self):
        """Unicode representation. """
        return '{course_id}, {certificate_type}'.format(
            course_id=self.course_id,
            certificate_type=self.certificate_type,
        )


class ProgramCertificate(AbstractCertificate):
    """
    Configuration for Program Certificates.
    """
    program_id = models.PositiveIntegerField(db_index=True)

    def __unicode__(self):
        """Unicode representation. """
        return '{program_id}'.format(
            program_id=self.program_id
        )


class UserCredential(TimeStampedModel):
    """
    Credentials issued to a learner.
    """
    AWARDED, REVOKED = (
        'awarded', 'revoked',
    )

    STATUSES_CHOICES = (
        (AWARDED, _('awarded')),
        (REVOKED, _('revoked')),
    )

    credential_content_type = models.ForeignKey(ContentType)
    credential_id = models.PositiveIntegerField()
    credential = GenericForeignKey('credential_content_type', 'credential_id')

    username = models.CharField(max_length=255, db_index=True)
    status = models.CharField(
        max_length=255,
        choices=STATUSES_CHOICES,
        default=AWARDED
    )
    download_url = models.CharField(
        max_length=255, blank=True, null=True,
        help_text=_('Download URL for the PDFs.')
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta(object):
        unique_together = (('username', 'credential_content_type', 'credential_id'),)

    def __unicode__(self):
        """Unicode representation. """
        return '{username}, {status}'.format(
            username=self.username,
            status=self.status
        )


class UserCredentialAttribute(TimeStampedModel):
    """
    Different attributes of User's Credential such as white list, grade etc.
    """
    user_credential = models.ForeignKey(UserCredential, related_name='attributes')
    namespace = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    def __unicode__(self):
        """Unicode representation. """
        return '{user_credential}, {namespace}, {name}'.format(
            user_credential=self.user_credential,
            namespace=self.namespace,
            name=self.name
        )


class CertificateTemplateAsset(TimeStampedModel):
    """
    Certificate Template Asset model to add content files for a certificate
    template.
    """
    name = models.CharField(max_length=255)
    asset_file = models.FileField(
        max_length=255,
        upload_to=assets_path,
        help_text=_('Asset file. It could be an image or css file.'),
    )

    def __unicode__(self):
        """Unicode representation. """
        return '{name}'.format(
            name=self.name
        )

    def save(self, *args, **kwargs):
        """Save the certificate template asset."""
        if self.pk is None:
            temp_file = self.asset_file
            self.asset_file = None
            super(CertificateTemplateAsset, self).save(*args, **kwargs)
            self.asset_file = temp_file

        super(CertificateTemplateAsset, self).save(*args, **kwargs)
