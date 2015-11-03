"""
Database models for the badges app
"""
from importlib import import_module

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from lazy import lazy

from xmodule_django.models import CourseKeyField
from jsonfield import JSONField


def validate_badge_image(image):
    """
    Validates that a particular image is small enough, of the right type, and square to be a badge.
    """
    if image.width != image.height:
        raise ValidationError(_(u"The badge image must be square."))
    if not image.size < (250 * 1024):
        raise ValidationError(_(u"The badge image file size must be less than 250KB."))


def validate_lowercase(string):
    """
    Validates that a string is lowercase.
    """
    if not string == string.lower():
        raise ValidationError(_(u"This value must be all lowercase."))


class BadgeClass(models.Model):
    """
    Specifies a badge class to be registered with a backend.
    """
    slug = models.SlugField(max_length=255, validators=[validate_lowercase])
    issuing_component = models.SlugField(max_length=50, default='', blank=True, validators=[validate_lowercase])
    display_name = models.CharField(max_length=255)
    course_id = CourseKeyField(max_length=255, blank=True, default=None)
    description = models.TextField()
    criteria = models.TextField()
    # Mode a badge was awarded for. Included for legacy/migration purposes.
    mode = models.CharField(max_length=100, default='', blank=True)
    image = models.ImageField(upload_to='badge_classes', validators=[validate_badge_image])

    def __unicode__(self):
        return u"<Badge '{slug}' for '{issuing_component}'>".format(
            slug=self.slug, issuing_component=self.issuing_component
        )

    @classmethod
    def get_badge_class(
            cls, slug, issuing_component, display_name, description, criteria, image_file_handle,
            mode='', course_id=None, create=True
    ):
        """
        Looks up a badge class by its slug, issuing component, and course_id and returns it should it exist.
        If it does not exist, and create is True, creates it according to the arguments. Otherwise, returns None.
        """
        slug = slug.lower()
        issuing_component = issuing_component.lower()
        if not course_id:
            course_id = CourseKeyField.Empty
        try:
            return cls.objects.get(slug=slug, issuing_component=issuing_component, course_id=course_id)
        except cls.DoesNotExist:
            if not create:
                return None
        badge_class = cls(
            slug=slug,
            issuing_component=issuing_component,
            display_name=display_name,
            course_id=course_id,
            mode=mode,
            description=description,
            criteria=criteria,
        )
        badge_class.image.save(image_file_handle.name, image_file_handle)
        badge_class.full_clean()
        badge_class.save()
        return badge_class

    @lazy
    def backend(self):
        """
        Loads the badging backend.
        """
        module, klass = settings.BADGING_BACKEND.rsplit('.', 1)
        module = import_module(module)
        return getattr(module, klass)()

    def get_for_user(self, user):
        """
        Get the assertion for this badge class for this user, if it has been awarded.
        """
        return self.badgeassertion_set.filter(user=user)

    def award(self, user, evidence_url=None):
        """
        Contacts the backend to have a badge assertion created for this badge class for this user.
        """
        return self.backend.award(self, user, evidence_url=evidence_url)

    def save(self, **kwargs):
        """
        Slugs must always be lowercase.
        """
        self.slug = self.slug and self.slug.lower()
        self.issuing_component = self.issuing_component and self.issuing_component.lower()
        super(BadgeClass, self).save(**kwargs)

    class Meta(object):
        app_label = "badges"
        unique_together = (('slug', 'issuing_component', 'course_id'),)


class BadgeAssertion(models.Model):
    """
    Tracks badges on our side of the badge baking transaction
    """
    user = models.ForeignKey(User)
    badge_class = models.ForeignKey(BadgeClass)
    data = JSONField()
    backend = models.CharField(max_length=50)
    image_url = models.URLField()
    assertion_url = models.URLField()

    def __unicode__(self):
        return u"<{username} Badge Assertion for {slug} for {issuing_component}".format(
            username=self.user.username, slug=self.badge_class.slug,
            issuing_component=self.badge_class.issuing_component,
        )

    @classmethod
    def assertions_for_user(cls, user, course_id=None):
        """
        Get all assertions for a user, optionally constrained to a course.
        """
        if course_id:
            return cls.objects.filter(user=user, badge_class__course_id=course_id)
        return cls.objects.filter(user=user)

    class Meta(object):
        app_label = "badges"


class CourseCompleteImageConfiguration(models.Model):
    """
    Contains the icon configuration for badges for a specific course mode.
    """
    mode = models.CharField(
        max_length=125,
        help_text=_(u'The course mode for this badge image. For example, "verified" or "honor".'),
        unique=True,
    )
    icon = models.ImageField(
        # Actual max is 256KB, but need overhead for badge baking. This should be more than enough.
        help_text=_(
            u"Badge images must be square PNG files. The file size should be under 250KB."
        ),
        upload_to='course_complete_badges',
        validators=[validate_badge_image]
    )
    default = models.BooleanField(
        help_text=_(
            u"Set this value to True if you want this image to be the default image for any course modes "
            u"that do not have a specified badge image. You can have only one default image."
        ),
        default=False,
    )

    def __unicode__(self):
        return u"<CourseCompleteImageConfiguration for '{mode}'{default}>".format(
            mode=self.mode,
            default=u" (default)" if self.default else u''
        )

    def clean(self):
        """
        Make sure there's not more than one default.
        """
        # pylint: disable=no-member
        if self.default and CourseCompleteImageConfiguration.objects.filter(default=True).exclude(id=self.id):
            raise ValidationError(_(u"There can be only one default image."))

    @classmethod
    def image_for_mode(cls, mode):
        """
        Get the image for a particular mode.
        """
        try:
            return cls.objects.get(mode=mode).icon
        except cls.DoesNotExist:
            # Fall back to default, if there is one.
            return cls.objects.get(default=True).icon

    class Meta(object):
        app_label = "badges"
