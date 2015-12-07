"""
Models for the credentials service.
"""
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from model_utils.models import TimeStampedModel
from xmodule_django.models import CourseKeyField


MODE_CHOICES = (
    (_('Honor'), 'honor'),
    (_('Verified'), 'verified'),
    (_('Professional'), 'professional'),
)


class AbstractCredential(TimeStampedModel):
    """
    Abstract Credentials configuration model to support multitenancy.
    """
    PROGRAMS, COURSES = (
        "programs", "courses",
    )
    TYPES_CHOICES = (
        (PROGRAMS, _("programs")),
        (COURSES, _("courses")),
    )

    credential_type = models.CharField(max_length=32, choices=TYPES_CHOICES, default=COURSES)
    site = models.ForeignKey('sites.Site', null=False, blank=False)
    is_active = models.BooleanField(default=False)

    def __unicode__(self):
        """Unicode representation. """
        return u"{site}, {credential_type}".format(
            site=self.site,
            credential_type=self.credential_type
        )


def assets_path(instance, filename):
    """
    Custom path for credentials templates and signatories file assets.

    Arguments:
        instance: CertificateTemplateAsset or Signatory object
        filename: file to upload

    Returns:
        Path of asset file e.g.
        credential_certificate_template_assets/1/filename,
        signatories/1/filename
    """

    path = 'credential_certificate_template_assets'
    if isinstance(instance, Signatory):
        path = 'signatories'

    name = os.path.join(
        path,
        str(instance.id),
        filename
    )
    fullname = os.path.join(settings.MEDIA_ROOT, name)
    if os.path.exists(fullname):
        os.remove(fullname)

    return name


def validate_image(image):
    """
    Validates that a particular image is small enough, of the right type and
    square to be a badge.
    """
    if image.width != image.height:
        raise ValidationError(_(u"The image must be square."))
    if image.size > (250 * 1024):
        raise ValidationError(_(u"The image file size must be less than 250KB."))


class Signatory(TimeStampedModel):
    """
    Signatory model to add certificate signatories.
    """
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    image = models.ImageField(
        help_text=_(
            u"Image must be square PNG files. The file size should be under 250KB."
        ),
        upload_to=assets_path,
        validators=[validate_image]
    )

    def __unicode__(self):
        """Unicode representation. """
        return u"{name}, {title}".format(
            name=self.name,
            title=self.title,
        )

    def save(self, *args, **kwargs):
        """save the certificate template asset """
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
        help_text=_(u"Template content data.")
    )
    certificate_type = models.CharField(
        max_length=32, null=True, blank=True,
        choices=MODE_CHOICES,
    )
    organization_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_(u'Organization of template.'),
    )

    def __unicode__(self):
        """Unicode representation. """
        return u"{name}".format(
            name=self.name
        )


class AbstractCertificate(AbstractCredential):
    """
    Abstract Certificate configuration to support multiple type of certificates
    i.e. Programs, Courses.
    """
    signatory = models.ForeignKey(Signatory)
    template = models.ForeignKey(CertificateTemplate, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)


class CourseCertificate(AbstractCertificate):
    """
    Configuration for Course Certificates.
    """
    course_id = CourseKeyField(max_length=255)
    certificate_type = models.CharField(
        max_length=32,
        choices=MODE_CHOICES
    )

    class Meta(object):
        # Enforce the constraint that mode and certificate should be unique
        # together.
        unique_together = (('course_id', 'certificate_type'),)

    def __unicode__(self):
        """Unicode representation. """
        return u"{course_id}, {certificate_type}".format(
            course_id=self.course_id,
            certificate_type=self.certificate_type,
        )


class ProgramCertificate(AbstractCertificate):
    """
    Configuration for Program Certificates.
    """
    program_id = models.IntegerField(
        db_index=True,
        unique=True,
        help_text=_(u'Programs Id.'),
    )

    def __unicode__(self):
        """Unicode representation. """
        return u"{program_id}".format(
            program_id=self.program_id
        )


class UserCredential(TimeStampedModel):
    """
    Credentials related to a learner.
    """
    AWARDED, REVOKED = (
        "awarded", "revoked",
    )

    STATUSES_CHOICES = (
        (AWARDED, _("awarded")),
        (REVOKED, _("revoked")),

    )

    username = models.CharField(max_length=255, db_index=True)
    credential = models.ForeignKey(AbstractCredential)
    status = models.CharField(
        max_length=32,
        choices=STATUSES_CHOICES,
        default=AWARDED
    )
    download_url = models.CharField(
        max_length=128, blank=True, null=True,
        help_text=_("Download URL for the PDFs.")
    )
    uuid = models.CharField(max_length=32)

    def __unicode__(self):
        """Unicode representation. """
        return u"{username}, {status}".format(
            username=self.username,
            status=self.status
        )


class UserCredentialAttribute(UserCredential):
    namespace = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    def __unicode__(self):
        """Unicode representation. """
        return u"{namespace}, {name}".format(
            namespace=self.namespace,
            name=self.name
        )


class CertificateTemplateAsset(TimeStampedModel):
    """
    Certificate Template Asset model to organize content for certificate
    templates.
    """
    name = models.CharField(max_length=255)
    asset_file = models.FileField(
        max_length=255,
        upload_to=assets_path,
        help_text=_(u'Asset file. It could be an image or css file.'),
    )

    def __unicode__(self):
        """Unicode representation. """
        return u"{name}".format(
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
