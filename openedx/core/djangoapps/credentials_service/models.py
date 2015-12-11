"""
Models for the credentials service.
"""
from __future__ import unicode_literals
import uuid  # pylint: disable=unused-import

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.generic import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from model_utils.models import TimeStampedModel


MODE_CHOICES = (
    (_('Honor'), 'honor'),
    (_('Verified'), 'verified'),
    (_('Professional'), 'professional'),
)


def template_assets_path(instance, filename):
    """
    Returns path for credentials templates file assets.

    Arguments:
        instance(CertificateTemplateAsset): CertificateTemplateAsset object
        filename(str): file to upload

    Returns:
        Path to asset.
    """

    return 'certificate_template_assets/{id}/{filename}'.format(id=instance.id, filename=filename)


def signatory_assets_path(instance, filename):
    """
    Returns path for signatory assets.

    Arguments:
        instance(Signatory): Signatory object
        filename(str): file to upload

    Returns:
        Path to asset.
    """
    return 'signatories/{id}/{filename}'.format(id=instance.id, filename=filename)


def validate_image(image):
    """
    Validates that a particular image is small enough.
    """
    if image.size > (250 * 1024):
        raise ValidationError(_('The image file size must be less than 250KB.'))


def validate_course_key(course_key):
    """
    Validate the course_key is correct.
    """
    try:
        CourseKey.from_string(course_key)
    except InvalidKeyError:
        raise ValidationError(_("Invalid course key."))


class SiteConfiguration(models.Model):
    """
    Custom Site model for custom sites/microsites.
    """
    site = models.OneToOneField('sites.Site', null=False, blank=False)
    lms_url_root = models.URLField(
        verbose_name=_('LMS base url for custom site/microsite'),
        help_text=_("Root URL of this site's LMS (e.g. https://courses.stage.edx.org)"),
        null=False,
        blank=False
    )
    theme_scss_path = models.CharField(
        verbose_name=_('Path to custom site theme'),
        help_text=_('Path to scss files of the custom site theme'),
        max_length=255,
        null=False,
        blank=False
    )

    def __unicode__(self):
        """Unicode representation. """
        return 'Site Configuration {site}'.format(
            site=self.site
        )


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
        upload_to=signatory_assets_path,
        validators=[validate_image]
    )

    def __unicode__(self):
        """Unicode representation. """
        return 'Signatory {name}, {title}'.format(
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
        else:
            super(Signatory, self).save(*args, **kwargs)


# pylint: disable=model-missing-unicode
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


class AbstractCertificate(AbstractCredential):
    """
    Abstract Certificate configuration to support multiple type of certificates
    i.e. Programs, Courses.
    """
    signatories = models.ManyToManyField(Signatory)
    template = models.ForeignKey(CertificateTemplate, null=True, blank=True)
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
    course_id = models.CharField(max_length=255, validators=[validate_course_key])
    certificate_type = models.CharField(
        max_length=255,
        choices=MODE_CHOICES
    )

    class Meta(object):
        unique_together = (('course_id', 'certificate_type', 'site'),)

    def __unicode__(self):
        """Unicode representation. """
        return 'CourseCertificate {course_id}, {certificate_type}'.format(
            course_id=self.course_id,
            certificate_type=self.certificate_type,
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


class ProgramCertificate(AbstractCertificate):
    """
    Configuration for Program Certificates.
    """
    program_id = models.PositiveIntegerField(db_index=True, unique=True)
    user_credentials = GenericRelation(
        UserCredential,
        content_type_field='credential_content_type',
        object_id_field='credential_id'
    )

    def __unicode__(self):
        """Unicode representation. """
        return 'ProgramCertificate for program {program_id}'.format(
            program_id=self.program_id
        )



class UserCredentialAttribute(TimeStampedModel):
    """
    Different attributes of User's Credential such as white list, grade etc.
    """
    user_credential = models.ForeignKey(UserCredential, related_name='attributes')
    namespace = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)


class CertificateTemplateAsset(TimeStampedModel):
    """
    Certificate Template Asset model to add content files for a certificate
    template.
    """
    name = models.CharField(max_length=255)
    asset_file = models.FileField(upload_to=template_assets_path)

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
        else:
            super(CertificateTemplateAsset, self).save(*args, **kwargs)
