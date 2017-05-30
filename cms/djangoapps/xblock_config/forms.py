"""
Defines a form for providing validation of LTI consumer course-specific configuration.
"""
import logging

from django import forms
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseLocator

from xblock_config.models import CourseEditLTIFieldsEnabledFlag
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


class CourseEditLTIFieldsEnabledAdminForm(forms.ModelForm):
    """
    Form for LTI consumer course-specific configuration to verify the course id.
    """

    class Meta(object):
        model = CourseEditLTIFieldsEnabledFlag
        fields = '__all__'

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
