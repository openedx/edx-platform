"""
Defines a form for providing validation.
"""
import logging

from django import forms

from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseLocator
from xmodule.modulestore.django import modulestore

from adaptive_learning.config.models import CourseAdaptiveLearningFlag

log = logging.getLogger(__name__)


class CourseAdaptiveLearningFlagForm(forms.ModelForm):
    """
    Input form for new AdaptiveLearning per-course enablement,
    allowing us to verify user input.
    """

    class Meta(object):
        model = CourseAdaptiveLearningFlag
        fields = '__all__'

    def clean_course_id(self):
        """Validate the course id"""
        cleaned_id = self.cleaned_data["course_id"]
        try:
            course_key = CourseLocator.from_string(cleaned_id)
        except InvalidKeyError:
            msg = u'Course id invalid. Entered course id was: "{0}."'.format(cleaned_id)
            raise forms.ValidationError(msg)

        if not modulestore().has_course(course_key):
            msg = u'Course not found. Entered course id was: "{0}". '.format(course_key.to_deprecated_string())
            raise forms.ValidationError(msg)

        return course_key
