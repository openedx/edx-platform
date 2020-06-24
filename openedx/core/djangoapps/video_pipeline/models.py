"""
Model to hold edx-video-pipeline configurations.
"""

from config_models.models import ConfigurationModel
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from opaque_keys.edx.django.models import CourseKeyField
import six


class VideoPipelineIntegration(ConfigurationModel):
    """
    Manages configuration for connecting to the edx-video-pipeline service and using its API.

    .. no_pii:
    """
    client_name = models.CharField(
        max_length=100,
        default=u'VEDA-Prod',
        null=False,
        blank=False,
        help_text=_('Oauth client name of video pipeline service.')
    )

    api_url = models.URLField(
        verbose_name=_('Internal API URL'),
        help_text=_('edx-video-pipeline API URL.')
    )

    service_username = models.CharField(
        max_length=100,
        default=u'veda_service_user',
        null=False,
        blank=False,
        help_text=_('Username created for Video Pipeline Integration, e.g. veda_service_user.')
    )

    def get_service_user(self):
        # NOTE: We load the user model here to avoid issues at startup time that result from the hacks
        # in lms/startup.py.
        User = get_user_model()  # pylint: disable=invalid-name
        return User.objects.get(username=self.service_username)


class VEMPipelineIntegration(ConfigurationModel):
    """
    Manages configuration for connecting to the video encode manager service and using its API.

    .. no_pii:
    """
    client_name = models.CharField(
        max_length=100,
        default='VEM-Prod',
        null=False,
        blank=False,
        help_text=_('Oauth client name of VEM service.')
    )

    api_url = models.URLField(
        verbose_name=_('Internal API URL'),
        help_text=_('video encode manager API URL.')
    )

    service_username = models.CharField(
        max_length=100,
        default='vem_service_user',
        null=False,
        blank=False,
        help_text=_('Username created for VEM Integration, e.g. vem_service_user.')
    )

    def get_service_user(self):
        User = get_user_model()  # pylint: disable=invalid-name
        return User.objects.get(username=self.service_username)


@python_2_unicode_compatible
class VideoUploadsEnabledByDefault(ConfigurationModel):
    """
    Enables video uploads enabled By default feature across the platform.

    .. no_pii:
    """
    # this field overrides course-specific settings
    enabled_for_all_courses = models.BooleanField(default=False)

    @classmethod
    def feature_enabled(cls, course_id):
        """
        Looks at the currently active configuration model to determine whether
        the VideoUploadsEnabledByDefault feature is available.

        If the feature flag is not enabled, the feature is not available.
        If the flag is enabled for all the courses, feature is available.
        If the flag is enabled and the provided course_id is for a course
            with CourseVideoUploadsEnabledByDefault enabled, then the
            feature is available.

        Arguments:
            course_id (CourseKey): course id for whom feature will be checked.
        """
        if not cls.is_enabled():
            return False
        elif not cls.current().enabled_for_all_courses:
            feature = (CourseVideoUploadsEnabledByDefault.objects
                       .filter(course_id=course_id)
                       .order_by('-change_date')
                       .first())
            return feature.enabled if feature else False
        return True

    def __str__(self):
        current_model = VideoUploadsEnabledByDefault.current()
        return u"VideoUploadsEnabledByDefault: enabled {is_enabled}".format(
            is_enabled=current_model.is_enabled()
        )


@python_2_unicode_compatible
class CourseVideoUploadsEnabledByDefault(ConfigurationModel):
    """
    Enables video uploads enabled by default feature for a specific course. Its global feature must be
    enabled for this to take effect.

    .. no_pii:
    """
    KEY_FIELDS = ('course_id',)

    course_id = CourseKeyField(max_length=255, db_index=True)

    def __str__(self):
        not_en = "Not "
        if self.enabled:
            not_en = ""

        return u"Course '{course_key}': Video Uploads {not_enabled}Enabled by default.".format(
            course_key=six.text_type(self.course_id),
            not_enabled=not_en
        )
