"""
Database models for the badges app
"""


from importlib import import_module

import six
from config_models.models import ConfigurationModel
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from lazy import lazy
from model_utils.models import TimeStampedModel
from opaque_keys import InvalidKeyError
from opaque_keys.edx.django.models import CourseKeyField
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.badges.utils import deserialize_count_specs
from openedx.core.djangolib.markup import HTML, Text
from xmodule.modulestore.django import modulestore


def validate_badge_image(image):
    """
    Validates that a particular image is small enough to be a badge and square.
    """
    if image.width != image.height:
        raise ValidationError(_(u"The badge image must be square."))
    if not image.size < (250 * 1024):
        raise ValidationError(_(u"The badge image file size must be less than 250KB."))


def validate_lowercase(string):
    """
    Validates that a string is lowercase.
    """
    if not string.islower():
        raise ValidationError(_(u"This value must be all lowercase."))


class CourseBadgesDisabledError(Exception):
    """
    Exception raised when Course Badges aren't enabled, but an attempt to fetch one is made anyway.
    """


@python_2_unicode_compatible
class BadgeClass(models.Model):
    """
    Specifies a badge class to be registered with a backend.

    .. no_pii:
    """
    slug = models.SlugField(max_length=255, validators=[validate_lowercase])
    issuing_component = models.SlugField(max_length=50, default=u'', blank=True, validators=[validate_lowercase])
    display_name = models.CharField(max_length=255)
    course_id = CourseKeyField(max_length=255, blank=True, default=None)
    description = models.TextField()
    criteria = models.TextField()
    # Mode a badge was awarded for. Included for legacy/migration purposes.
    mode = models.CharField(max_length=100, default=u'', blank=True)
    image = models.ImageField(upload_to=u'badge_classes', validators=[validate_badge_image])

    def __str__(self):
        return HTML(u"<Badge '{slug}' for '{issuing_component}'>").format(
            slug=HTML(self.slug), issuing_component=HTML(self.issuing_component)
        )

    @classmethod
    def get_badge_class(
            cls, slug, issuing_component, display_name=None, description=None, criteria=None, image_file_handle=None,
            mode='', course_id=None, create=True
    ):
        """
        Looks up a badge class by its slug, issuing component, and course_id and returns it should it exist.
        If it does not exist, and create is True, creates it according to the arguments. Otherwise, returns None.

        The expectation is that an XBlock or platform developer should not need to concern themselves with whether
        or not a badge class has already been created, but should just feed all requirements to this function
        and it will 'do the right thing'. It should be the exception, rather than the common case, that a badge class
        would need to be looked up without also being created were it missing.
        """
        slug = slug.lower()
        issuing_component = issuing_component.lower()
        if course_id and not modulestore().get_course(course_id).issue_badges:
            raise CourseBadgesDisabledError("This course does not have badges enabled.")
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
        verbose_name_plural = "Badge Classes"


@python_2_unicode_compatible
class BadgeAssertion(TimeStampedModel):
    """
    Tracks badges on our side of the badge baking transaction

    .. no_pii:
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge_class = models.ForeignKey(BadgeClass, on_delete=models.CASCADE)
    data = JSONField()
    backend = models.CharField(max_length=50)
    image_url = models.URLField()
    assertion_url = models.URLField()

    def __str__(self):
        return HTML(u"<{username} Badge Assertion for {slug} for {issuing_component}").format(
            username=HTML(self.user.username),
            slug=HTML(self.badge_class.slug),
            issuing_component=HTML(self.badge_class.issuing_component),
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


# Abstract model doesn't index this, so we have to.
BadgeAssertion._meta.get_field('created').db_index = True


@python_2_unicode_compatible
class CourseCompleteImageConfiguration(models.Model):
    """
    Contains the icon configuration for badges for a specific course mode.

    .. no_pii:
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
        upload_to=u'course_complete_badges',
        validators=[validate_badge_image]
    )
    default = models.BooleanField(
        help_text=_(
            u"Set this value to True if you want this image to be the default image for any course modes "
            u"that do not have a specified badge image. You can have only one default image."
        ),
        default=False,
    )

    def __str__(self):
        return HTML(u"<CourseCompleteImageConfiguration for '{mode}'{default}>").format(
            mode=HTML(self.mode),
            default=HTML(u" (default)") if self.default else HTML(u'')
        )

    def clean(self):
        """
        Make sure there's not more than one default.
        """
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


@python_2_unicode_compatible
class CourseEventBadgesConfiguration(ConfigurationModel):
    """
    Determines the settings for meta course awards-- such as completing a certain
    number of courses or enrolling in a certain number of them.

    .. no_pii:
    """
    courses_completed = models.TextField(
        blank=True, default=u'',
        help_text=_(
            u"On each line, put the number of completed courses to award a badge for, a comma, and the slug of a "
            u"badge class you have created that has the issuing component 'openedx__course'. "
            u"For example: 3,enrolled_3_courses"
        )
    )
    courses_enrolled = models.TextField(
        blank=True, default=u'',
        help_text=_(
            u"On each line, put the number of enrolled courses to award a badge for, a comma, and the slug of a "
            u"badge class you have created that has the issuing component 'openedx__course'. "
            u"For example: 3,enrolled_3_courses"
        )
    )
    course_groups = models.TextField(
        blank=True, default=u'',
        help_text=_(
            u"Each line is a comma-separated list. The first item in each line is the slug of a badge class you "
            u"have created that has an issuing component of 'openedx__course'. The remaining items in each line are "
            u"the course keys the learner needs to complete to be awarded the badge. For example: "
            u"slug_for_compsci_courses_group_badge,course-v1:CompSci+Course+First,course-v1:CompsSci+Course+Second"
        )
    )

    def __str__(self):
        return HTML(u"<CourseEventBadgesConfiguration ({})>").format(
            Text(u"Enabled") if self.enabled else Text(u"Disabled")
        )

    @property
    def completed_settings(self):
        """
        Parses the settings from the courses_completed field.
        """
        return deserialize_count_specs(self.courses_completed)

    @property
    def enrolled_settings(self):
        """
        Parses the settings from the courses_completed field.
        """
        return deserialize_count_specs(self.courses_enrolled)

    @property
    def course_group_settings(self):
        """
        Parses the course group settings. In example, the format is:

        slug_for_compsci_courses_group_badge,course-v1:CompSci+Course+First,course-v1:CompsSci+Course+Second
        """
        specs = self.course_groups.strip()
        if not specs:
            return {}
        specs = [line.split(',', 1) for line in specs.splitlines()]
        return {
            slug.strip().lower(): [CourseKey.from_string(key.strip()) for key in keys.strip().split(',')]
            for slug, keys in specs
        }

    def clean_fields(self, exclude=tuple()):
        """
        Verify the settings are parseable.
        """
        errors = {}
        error_message = _(u"Please check the syntax of your entry.")
        if 'courses_completed' not in exclude:
            try:
                self.completed_settings
            except (ValueError, InvalidKeyError):
                errors['courses_completed'] = [six.text_type(error_message)]
        if 'courses_enrolled' not in exclude:
            try:
                self.enrolled_settings
            except (ValueError, InvalidKeyError):
                errors['courses_enrolled'] = [six.text_type(error_message)]
        if 'course_groups' not in exclude:
            store = modulestore()
            try:
                for key_list in self.course_group_settings.values():
                    for course_key in key_list:
                        if not store.get_course(course_key):
                            ValueError(u"The course {course_key} does not exist.".format(course_key=course_key))
            except (ValueError, InvalidKeyError):
                errors['course_groups'] = [six.text_type(error_message)]
        if errors:
            raise ValidationError(errors)

    class Meta(object):
        app_label = "badges"
