"""
Defines a form for providing validation of HLS Playback course-specific configuration.
"""
import logging

from django import forms
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseLocator

from openedx.core.djangoapps.video_config.models import CourseHLSPlaybackEnabledFlag, CourseVideoTranscriptEnabledFlag
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


class CourseSpecificFlagAdminBaseForm(forms.ModelForm):
    """
    Form for course-specific feature configuration.
    """

    # Make abstract base class
    class Meta(object):
        abstract = True

    def clean_course_id(self):
        """
        Validate the course id
        """
        cleaned_id = self.cleaned_data["course_id"]
        try:
            course_key = CourseLocator.from_string(cleaned_id)
        except InvalidKeyError:
            msg = u'Course id invalid. Entered course id was: "{course_id}."'.format(
                course_id=cleaned_id
            )
            raise forms.ValidationError(msg)

        if not modulestore().has_course(course_key):
            msg = u'Course not found. Entered course id was: "{course_key}". '.format(
                course_key=unicode(course_key)
            )
            raise forms.ValidationError(msg)

        return course_key


class CourseHLSPlaybackFlagAdminForm(CourseSpecificFlagAdminBaseForm):
    """
    Form for course-specific HLS Playback configuration.
    """

    class Meta(object):
        model = CourseHLSPlaybackEnabledFlag
        fields = '__all__'


class CourseVideoTranscriptFlagAdminForm(CourseSpecificFlagAdminBaseForm):
    """
    Form for course-specific Video Transcript configuration.
    """

    class Meta(object):
        model = CourseVideoTranscriptEnabledFlag
        fields = '__all__'
